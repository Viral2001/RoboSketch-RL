"""
RoboSketch-RL  |  real camera-in-the-loop
-------------------------------------------------
A RealCamera renders an ACTUAL PyBullet camera looking at the paper and recovers
the drawing with OpenCV - the exact B6 pipeline - so the RL reward can come from
a real render, not the fast `_perceive()` approximation. This closes the
"simulated camera" caveat on the H2 result.

There is NO arm in this scene (the pen is kinematic), so nothing occludes the
paper - the camera sees the whole drawing top-down. The drawing is carried into
the scene as a texture on a UV-mapped paper mesh (a box would not map it; see
docs/RESEARCH_LOG.md), reloaded from disk each capture (changeTexture is a no-op
in this PyBullet build; loadTexture caches by filename, so filenames are unique).
"""
import os

import cv2
import numpy as np
import pybullet as p
import pybullet_data
from pybullet_utils import bullet_client

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER_OBJ = os.path.join(_ROOT, "assets", "paper_quad.obj")
_TMP = os.path.join(_ROOT, "output", "_camtmp")


class RealCamera:
    def __init__(self, canvas_res, paper_cx=0.55, paper_cy=0.0, paper_half=0.10,
                 paper_top_z=0.003, cam_res=480, instance=0):
        self.res = canvas_res
        self.cx, self.cy, self.half, self.top_z = paper_cx, paper_cy, paper_half, paper_top_z
        self.cam_res = cam_res
        self._n = 0
        self._id = instance
        os.makedirs(_TMP, exist_ok=True)

        self.bc = bullet_client.BulletClient(connection_mode=p.DIRECT)
        self.bc.setAdditionalSearchPath(pybullet_data.getDataPath())
        self.bc.loadURDF("plane.urdf")
        vis = self.bc.createVisualShape(p.GEOM_MESH, fileName=PAPER_OBJ,
                                        meshScale=[paper_half, paper_half, 1.0],
                                        rgbaColor=[1, 1, 1, 1])
        self.paper = self.bc.createMultiBody(baseMass=0, baseVisualShapeIndex=vis,
                                             basePosition=[paper_cx, paper_cy, paper_top_z])
        blank = np.full((canvas_res, canvas_res, 3), 255, np.uint8)
        self._path = self._write(blank)
        self.bc.changeVisualShape(self.paper, -1,
                                  textureUniqueId=self.bc.loadTexture(self._path))
        # top-down camera; up=+y matches the canvas convention (B6-verified)
        self.view = self.bc.computeViewMatrix([paper_cx, paper_cy, 0.55],
                                              [paper_cx, paper_cy, paper_top_z], [0, 1, 0])
        self.proj = self.bc.computeProjectionMatrixFOV(24, 1.0, 0.1, 1.0)

    def _write(self, img3):
        self._n += 1
        path = os.path.join(_TMP, f"cam{self._id}_{self._n:06d}.png")
        cv2.imwrite(path, img3)
        old = os.path.join(_TMP, f"cam{self._id}_{self._n - 3:06d}.png")
        if os.path.exists(old):
            try:
                os.remove(old)
            except OSError:
                pass
        return path

    def perceive(self, canvas):
        """canvas: (res,res) uint8, 255=ink. Returns perceived binary (255=ink)
        as recovered by a real camera render + OpenCV."""
        # paper is white with black ink: invert the ink mask
        paper_img = cv2.cvtColor(255 - canvas, cv2.COLOR_GRAY2BGR)
        path = self._write(paper_img)
        self.bc.changeVisualShape(self.paper, -1, textureUniqueId=self.bc.loadTexture(path))
        w, h, rgb, _, seg = self.bc.getCameraImage(
            self.cam_res, self.cam_res, self.view, self.proj,
            renderer=p.ER_TINY_RENDERER)
        rgb = np.reshape(np.array(rgb, np.uint8), (h, w, 4))[:, :, :3]
        seg = np.reshape(np.array(seg), (h, w))
        mask = (seg == self.paper)
        if mask.sum() < 50:
            return np.zeros((self.res, self.res), np.uint8)
        ys, xs = np.nonzero(mask)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        grey = cv2.cvtColor(rgb[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY)
        grey[~mask[y0:y1, x0:x1]] = 255
        _, binv = cv2.threshold(grey, 128, 255, cv2.THRESH_BINARY_INV)
        out = cv2.resize(binv, (self.res, self.res), interpolation=cv2.INTER_AREA)
        return (out > 40).astype(np.uint8) * 255

    def close(self):
        try:
            self.bc.disconnect()
        except Exception:
            pass
