"""
Shared display helpers for the RoboSketch-RL PyBullet windows.

Two small quality-of-life fixes, used by every sim script:

1. crisp_window()  - stop Windows blurring the 3D view.
   Windows 11 usually runs a laptop screen at 125-150% scaling. PyBullet's
   OpenGL window does not declare itself "DPI aware", so Windows renders it
   small and then STRETCHES the finished image up to fit - exactly like
   zooming into a photo, which is why everything looks soft. Declaring the
   process DPI-aware makes Windows hand us the real pixels instead.

2. tidy_panels() - hide the three empty "Synthetic Camera" preview panels
   that PyBullet shows by default. They are unused right now, they eat screen
   space, and rendering them costs frame rate.
"""
import sys


def crisp_window():
    """Tell Windows we handle high-DPI ourselves, so it stops upscaling us.

    Must be called BEFORE p.connect(p.GUI), i.e. before the window exists.
    Safe no-op on non-Windows systems and on older Windows versions.
    """
    if sys.platform != "win32":
        return
    import ctypes
    try:
        # 2 = per-monitor DPI aware (best; Windows 8.1+)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()   # older fallback
        except Exception:
            pass                                        # not fatal, just blurrier


def tidy_panels(p):
    """Hide the unused RGB / depth / segmentation preview panels."""
    p.configureDebugVisualizer(p.COV_ENABLE_RGB_BUFFER_PREVIEW, 0)
    p.configureDebugVisualizer(p.COV_ENABLE_DEPTH_BUFFER_PREVIEW, 0)
    p.configureDebugVisualizer(p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW, 0)


def label(text):
    """Pad a debug-GUI label so PyBullet does not eat its first character.

    PyBullet's debug panel draws label text shifted ~1 character to the left of
    its clipping box, so the FIRST character is always chopped: "joint_1" shows
    as "'oint_1", "Params" as "arams". This affects every label regardless of
    length, so shortening names does not help - but a leading space does: the
    space gets eaten instead of a real letter.

    (Only our own labels can be fixed this way. PyBullet's built-in File/View
    menus and Explorer/Test/Params tabs are drawn by the library's C++ code and
    are chopped the same way; we cannot reach them.)
    """
    return " " + text


def connect_gui(p, width=1600, height=950):
    """Open a PyBullet GUI window that is sharp and roomy, then tidy it.

    Does the three things every sim script needs, in the right order:
      1. declare DPI awareness  (must happen BEFORE the window exists)
      2. open the window at an explicit, generous size
      3. hide the unused camera preview panels

    Why the explicit size: PyBullet's side panel lays its widgets out in
    pixels and simply CHOPS any label too wide for its box - which is why the
    tabs read "xplorer"/"arams" and a slider named "lbr_iiwa_joint_1" shows as
    "br_iiwa_joint_1". A wider window gives those boxes more room. The rest of
    the cure is on us: keep slider names SHORT (see the scripts).
    """
    crisp_window()
    p.connect(p.GUI, options=f"--width={width} --height={height}")
    tidy_panels(p)
