import mediapipe as mp
print('version', mp.__version__)
print('file', mp.__file__)
print('has solutions', hasattr(mp, 'solutions'))
print('dir slice', [n for n in dir(mp) if 'solution' in n.lower() or 'task' in n.lower()][:80])
try:
    import mediapipe.tasks.python as tasks
    print('tasks ok', tasks)
    print('tasks dir', [n for n in dir(tasks) if 'vision' in n.lower() or 'face' in n.lower()][:80])
except Exception as e:
    print('tasks error', e)
