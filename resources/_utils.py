import string, random

def print_green(message):
    print(f"\033[92m{message}\033[0m")

def print_blue(message):
    print(f"\033[94m{message}\033[0m")

def print_red(message):
    print(f"\033[91m{message}\033[0m")

def print_yellow(message):
    print(f"\033[93;1m{message}\033[0m")

def print_magenta(message):
    print(f"\033[95m{message}\033[0m")

def get_random_2fa():
    characters = string.ascii_letters + string.digits
    two_fa_string = ''.join(random.choice(characters) for i in range(random.randrange(8,14)))
    return two_fa_string