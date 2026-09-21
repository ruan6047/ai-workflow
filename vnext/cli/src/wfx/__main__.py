"""`python -m wfx <verb> …`（卡 1 以 PYTHONPATH=vnext/cli/src 呼叫；console script 在卡 2）。"""
import sys

from wfx.verbs.main import main

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
