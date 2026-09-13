

def function_name(parameters):
    """
    Description of the function.

    Args:
        parameters: Description of the parameters.

    Returns:
        Description of the return value.
    """
    # Function implementation goes here
    pass


def welcome(name):
    print(f"Welcome, {name}!")


welcome("Alice")  # Example usage of the welcome function

# arguments-
# Positional arguments: These are the most common type of arguments. They are passed to a function in the order in which they are defined. For example:
# Default arguments: These are arguments that have a default value assigned to them. If the caller does not provide a value for that argument, the default value will be used. For example:
def greet(name, greeting="Hello"):
    print(f"{greeting}, {name}!")

# Keyword arguments: These are arguments that are passed to a function using the name of the parameter. This allows you to specify the value of an argument without having to worry about the order in which they are defined. For example:
def introduce(name, age):
    print(f"My name is {name} and I am {age} years old.")

# Arbitrary arguments: These are arguments that allow you to pass a variable number of arguments to a function. They are defined using an asterisk (*) before the parameter name. For example:
def sum_numbers(*numbers):
    total = sum(numbers)
    print(f"The sum of the numbers is: {total}")

# Arbitrary keyword arguments: These are arguments that allow you to pass a variable number of keyword arguments to a function. They are defined using two asterisks (**) before the parameter name. For example:
def print_info(**info):
    for key, value in info.items():
        print(f"{key}: {value}")

# Returning values
# single and multiple values: return a, return a, b, c

# Decorators: Decorators are a way to modify the behavior of a function without changing its code. They are defined using the @ symbol followed by the name of the decorator function. For example:
def decorator_function(original_function):
    def wrapper_function(*args, **kwargs):
        print("Before the function is called.")
        result = original_function(*args, **kwargs)
        print("After the function is called.")
        return result
    return wrapper_function

@decorator_function
def say_hello():
    print("Hello!")




