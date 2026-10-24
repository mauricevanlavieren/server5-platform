#!/usr/bin/env python3
"""Current Projects; reuse the proven Test Projects growth/pruning engine."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('project_engine',Path(__file__).with_name('test-projects.py'))
engine=importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
engine.STATE=engine.ROOT/'mindmap/public/current-projects.json'
from functools import partial
engine.update=partial(engine.update, independent=True)
engine.EVIDENCE=engine.ROOT/'docs/mindmaps/current-projects'
if __name__=='__main__': engine.main()
