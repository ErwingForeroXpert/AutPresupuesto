from utils.constants import ROOT_DIR, LOG_NAME

def exceptionHandler(func):
    """Manage Exceptions

    Args:
        func (function): callback function
    """
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _message = f"{func.__name__} - {e}"
            insertInLog(_message, LOG_NAME, "error")
            raise Exception(_message)
    return inner_function

def insertInLog(message, name, path: str = None, type="debug"):
    """Insert new line in file log

    Args:
        message (String): message
        type (str, optional): type of log. Defaults to "debug".
    """
    if not os.path.exists(path):
        raise ValueError("Invalid route of path")
        
    _path = os.path.normpath(os.path.join(ROOT_DIR if path is None else path, f'{name}.log'))
    logging.basicConfig(filename=_path, encoding='utf-8', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
    loger = {
        "debug": logging.debug,
        "warning": logging.warning,
        "info": logging.info,
        "error": logging.error,
    }[type]

    loger(f"{datetime.now().strftime(r'%d/%m/%Y %H:%M:%S')} {message} \n")
    print(f"{datetime.now().strftime(r'%d/%m/%Y %H:%M:%S')} {message} \n")