import sys, importlib.util as u
sys.path.insert(0, '.')
fails = 0
for t in ["test_consistency_skill102", "test_skill102_consistency", "test_api", "test_app", "test_telegram_approvals"]:
    try:
        s = u.spec_from_file_location(t, f'tests/{t}.py')
        m = u.module_from_spec(s); s.loader.exec_module(m)
        for n in dir(m):
            f = getattr(m, n)
            if n.startswith('test_') and callable(f) and getattr(f, '__code__', None) and f.__code__.co_argcount == 0:
                f()
        print('PASS', t)
    except BaseException as e:
        fails += 1
        print('FAIL', t, type(e).__name__, e)
print('FAILS', fails)
