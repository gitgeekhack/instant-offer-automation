import os
import sys
import logging


class PackagePathFilter(logging.Filter):
    def filter(self, record):
        pathname = record.pathname
        abs_sys_paths = map(os.path.abspath, sys.path)
        for path in sorted(abs_sys_paths, key=len, reverse=True):  # longer paths first
            if not path.endswith(os.sep):
                path += os.sep
            if pathname.startswith(path):
                record.pathname = os.path.relpath(pathname, path).replace('/', '.').replace('\\', '.')
                break
        return True


def get_logger():
    logger = logging.getLogger('instant-offer-automation')
    logging.basicConfig(level=logging.INFO, format='[Time: %(asctime)s] - '
                                                   '[Logger: %(name)s] - '
                                                   '[Level: %(levelname)s] - '
                                                   '[Module: %(pathname)s] - '
                                                   '[Function: %(funcName)s] - '
                                                   '%(message)s')
    logger.addFilter(PackagePathFilter())
    return logger


logger = get_logger()
