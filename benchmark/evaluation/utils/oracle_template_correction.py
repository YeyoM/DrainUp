# Original: University of Luxembourg (TA-Eval-Rep). See NOTICE.

from __future__ import print_function

import os
from evaluation.utils.common import correct_templates_and_update_files, datasets


def main():
    for system in datasets:
        print('-' * 70)
        print(system)
        dir_path = os.path.join('..', 'logs', system)
        log_file_basename = system + '_2k.log'
        correct_templates_and_update_files(dir_path, log_file_basename, inplace=False)


if __name__ == '__main__':
    main()

