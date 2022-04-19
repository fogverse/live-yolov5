import os
import re
import unittest

from pathlib import Path

def get_test_suites(re_pattern='test\w*.py', exclude=[]):
    regex = re.compile(re_pattern)

    cwd = Path('.').resolve()
    script_file = os.path.relpath(__file__)
    exclude.append(script_file)

    module_names = []
    for root, _, files in os.walk('.', topdown=True):
        if root == '.': continue
        root = Path(root).resolve().relative_to(cwd)
        if str(root) in exclude: continue
        for file in files:
            file_relative = str(root/file)
            if file_relative in exclude: continue
            if not regex.match(file): continue
            module_name = file_relative.replace('/','.').replace('.py','')
            module_names.append(module_name)

    suites = unittest.defaultTestLoader.loadTestsFromNames(module_names)
    return unittest.TestSuite(suites)

def main():
    exclude = ['fogverse', '.git']
    test_suites = get_test_suites(exclude=exclude)
    runner = unittest.TextTestRunner()
    runner.run(test_suites)

if __name__ == '__main__':
    main()
