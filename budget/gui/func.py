from tkinter import messagebox

def decorator_exception_message(func, title: str):
    """Create exception message for the decorated function.

    Args:
        func (function): middle function
        title (str): title of project
    """
    def function_wrapper(*args, **kargs):
        try:
            func(*args, **kargs)
        except Exception as e:
            messagebox.askokcancel(message=f"{e}", title=title)
            print(f"Exception found in {func.__name__}, {e}")
    return function_wrapper