"""Atlas 3D OpenGL scene embedded in the Learning OS dashboard.

The renderer owns a real OpenGL context through pyopengltk.OpenGLFrame.
It deliberately keeps the dashboard controls in CustomTkinter while the
central Atlas visualization is rendered with depth, perspective and 3D
geometry.
"""
from __future__ import annotations

import math
import time

from pyopengltk import OpenGLFrame
from OpenGL import GL, GLU


class Atlas3DView(OpenGLFrame):
    """Lightweight real-time 3D Atlas core for Tk/CustomTkinter."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.animate = 1
        self.started = time.perf_counter()
        self.angle = 0.0
        self.width = max(1, int(kwargs.get("width", 900)))
        self.height = max(1, int(kwargs.get("height", 650)))
        self.particles = self._make_particles(90)

    @staticmethod
    def _make_particles(count):
        particles = []
        # Deterministic distribution: stable visual, no runtime randomness.
        for i in range(count):
            a = (i * 2.399963229728653) % (math.tau)
            b = ((i * 1.618033988749895) % 1.0 - 0.5) * math.pi
            radius = 2.5 + (i % 17) * 0.18
            particles.append((
                math.cos(a) * math.cos(b) * radius,
                math.sin(b) * radius * 0.72,
                math.sin(a) * math.cos(b) * radius,
                1.5 + (i % 4) * 0.35,
            ))
        return particles

    def initgl(self):
        GL.glClearColor(0.008, 0.012, 0.035, 1.0)
        GL.glClearDepth(1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_POINT_SMOOTH)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glDisable(GL.GL_CULL_FACE)
        self._set_projection()
        try:
            version = GL.glGetString(GL.GL_VERSION)
            renderer = GL.glGetString(GL.GL_RENDERER)
            print(
                "ATLAS_OPENGL_CONTEXT:",
                version.decode(errors="replace") if version else "unknown",
                "|",
                renderer.decode(errors="replace") if renderer else "unknown",
            )
        except Exception:
            pass

    def _set_projection(self):
        width = max(1, int(getattr(self, "width", 1)))
        height = max(1, int(getattr(self, "height", 1)))
        GL.glViewport(0, 0, width, height)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(42.0, width / float(height), 0.1, 100.0)
        GL.glMatrixMode(GL.GL_MODELVIEW)

    def resize(self, width, height):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        try:
            self._set_projection()
        except Exception:
            pass

    def _sphere(self, radius=1.0, lat=22, lon=36):
        for i in range(lat):
            t0 = math.pi * (-0.5 + i / lat)
            t1 = math.pi * (-0.5 + (i + 1) / lat)
            z0, zr0 = math.sin(t0), math.cos(t0)
            z1, zr1 = math.sin(t1), math.cos(t1)
            GL.glBegin(GL.GL_QUAD_STRIP)
            for j in range(lon + 1):
                p = math.tau * j / lon
                cp, sp = math.cos(p), math.sin(p)
                for z, zr in ((z1, zr1), (z0, zr0)):
                    x, y = cp * zr, sp * zr
                    GL.glNormal3f(x, y, z)
                    GL.glVertex3f(radius * x, radius * y, radius * z)
            GL.glEnd()

    def _ring(self, radius, tilt_x, tilt_z, alpha=0.65, segments=160):
        GL.glPushMatrix()
        GL.glRotatef(tilt_x, 1.0, 0.0, 0.0)
        GL.glRotatef(tilt_z, 0.0, 0.0, 1.0)
        GL.glBegin(GL.GL_LINE_LOOP)
        for i in range(segments):
            a = math.tau * i / segments
            GL.glVertex3f(math.cos(a) * radius, math.sin(a) * radius * 0.30, 0.0)
        GL.glEnd()
        GL.glPopMatrix()

    def _platform(self):
        GL.glPushMatrix()
        GL.glTranslatef(0.0, -2.0, 0.0)
        for scale, alpha in ((2.9, 0.28), (2.35, 0.42), (1.8, 0.55)):
            GL.glColor4f(0.24, 0.38, 1.0, alpha)
            GL.glBegin(GL.GL_LINE_LOOP)
            for i in range(120):
                a = math.tau * i / 120
                GL.glVertex3f(
                    math.cos(a) * scale,
                    math.sin(a) * scale * 0.20,
                    math.sin(a) * scale * 0.04,
                )
            GL.glEnd()
        GL.glColor4f(0.40, 0.50, 1.0, 0.25)
        GL.glBegin(GL.GL_LINES)
        for i in range(-8, 9):
            x = i * 0.32
            GL.glVertex3f(x, -0.02, -2.0)
            GL.glVertex3f(x, -0.02, 2.0)
        GL.glEnd()
        GL.glPopMatrix()

    def _particles(self):
        GL.glPointSize(2.2)
        GL.glBegin(GL.GL_POINTS)
        for x, y, z, size in self.particles:
            # A little variation without textures.
            brightness = 0.45 + (size - 1.5) * 0.14
            GL.glColor4f(0.42, 0.62, 1.0, brightness)
            GL.glVertex3f(x, y, z)
        GL.glEnd()

    def redraw(self):
        # pyopengltk calls redraw with this widget's context current.
        self.angle += 0.45
        t = time.perf_counter() - self.started
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self._set_projection()

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GLU.gluLookAt(0.0, 0.6, 12.5, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        # Deep-space particle field.
        GL.glDisable(GL.GL_DEPTH_TEST)
        self._particles()
        GL.glEnable(GL.GL_DEPTH_TEST)

        # 3D orbital system.
        GL.glLineWidth(1.4)
        for radius, tx, tz, alpha in (
            (2.35, 66.0, self.angle * 0.55, 0.48),
            (3.05, 72.0, -self.angle * 0.42, 0.72),
            (3.80, 58.0, self.angle * 0.30 + 38.0, 0.45),
        ):
            GL.glColor4f(0.30, 0.42, 1.0, alpha)
            self._ring(radius, tx, tz, alpha)

        # Floating orbital nodes give the rings readable depth.
        GL.glPointSize(5.0)
        GL.glBegin(GL.GL_POINTS)
        for idx, radius in enumerate((2.35, 3.05, 3.80)):
            a = math.radians(self.angle * (0.8 + idx * 0.25) + idx * 120.0)
            x = math.cos(a) * radius
            y = math.sin(a) * radius * 0.30
            z = math.sin(a) * radius * 0.55
            GL.glColor4f(0.62, 0.70, 1.0, 0.95)
            GL.glVertex3f(x, y, z)
        GL.glEnd()

        # Soft atmospheric shells. Blending creates the halo without a 2D canvas.
        GL.glDepthMask(GL.GL_FALSE)
        for radius, alpha in ((2.05, 0.055), (1.82, 0.08), (1.62, 0.11)):
            GL.glColor4f(0.22, 0.28, 1.0, alpha)
            self._sphere(radius, 16, 28)
        GL.glDepthMask(GL.GL_TRUE)

        # Main solid 3D Atlas core.
        GL.glColor4f(0.10, 0.18, 0.58, 1.0)
        GL.glPushMatrix()
        GL.glRotatef(self.angle * 0.22, 0.0, 1.0, 0.0)
        self._sphere(1.48, 28, 44)
        GL.glPopMatrix()

        # Inner energy sphere.
        GL.glColor4f(0.18, 0.30, 0.95, 0.92)
        GL.glPushMatrix()
        GL.glRotatef(-self.angle * 0.35, 1.0, 0.0, 0.0)
        self._sphere(1.05, 24, 40)
        GL.glPopMatrix()

        # Small bright core.
        GL.glColor4f(0.52, 0.62, 1.0, 0.75)
        self._sphere(0.46, 18, 28)

        # Holographic platform.
        GL.glLineWidth(1.0)
        self._platform()

