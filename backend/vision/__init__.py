"""SENTINEL AI - computer vision package.

Modules degrade gracefully: if a heavy dependency (OpenCV / YOLO /
EasyOCR) is unavailable, the pipeline reports its absence and falls
back to Pillow-based metadata + heuristic analysis. The platform keeps
working everywhere; optional models only upgrade fidelity.
"""
