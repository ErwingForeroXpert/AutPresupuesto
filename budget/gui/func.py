from tkinter import messagebox

def decorator_exception_message(title: str):
    """Create exception message for the decorated function.

    Args:
        func (function): middle function
        title (str): title of project
    """
    def parent_wrapper(func):
        async def function_wrapper(*args, **kargs):
            try:
                await func(*args, **kargs)
            except Exception as e:
                messagebox.showerror(message=f"{e}", title=title)
                print(f"Exception found in {func.__name__}, {e}")
        return function_wrapper
        
    return parent_wrapper