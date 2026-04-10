import numpy as np


# Encoding-Decoding for Adjacency Matrix {{{


def binary_list_to_base16(binary_list):
    """Convert list in base2 to string in base16."""
    # Insert 1 at first position to not have trailing 0
    if isinstance(binary_list, list):
        binary_list.insert(0, 1)
    else:
        binary_list = np.insert(binary_list, 0, 1)
    # Convert binary list to a binary string
    binary_string = ''.join(map(str, binary_list))
    # Convert binary string to integer
    decimal_value = int(binary_string, 2)
    # Base-16 (hexadecimal)
    encoded_string = hex(decimal_value)[2:].upper()  # Remove '0x' prefix and convert to uppercase
    # Don't include first element because it's an artificial 1
    return encoded_string


def base16_decode_to_binary_list(b16_string):
    """Convert list in base16 to string in base2."""
    # Convert the hexadecimal string to an integer
    decimal_value = int(b16_string, 16)
    # Convert the integer to a binary string (remove the '0b' prefix)
    binary_string = bin(decimal_value)[2:]
    # Convert the binary string to a list of binary digits
    binary_list = [int(bit) for bit in binary_string]
    return binary_list[1:]

# }}}
# Encoding-Decoding for graph positions {{{


def encode_nested_numbers(nested_list):
    """Encode each sublist into a string, then join them with a delimiter (e.g., ";")."""
    return ';'.join(','.join(map(str, sublist)) for sublist in nested_list)


def decode_nested_numbers(encoded_str):
    """Split the string into sublists and convert back to numbers."""
    return [list(map(int, sublist.split(','))) for sublist in encoded_str.split(';')]

# }}}


if __name__ == '__main__':
    pass

    # # Example binary list
    # binary_list = [1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
    # base16_encoded = binary_list_to_base16(binary_list)
    # print(f"Base-16 encoding: {base16_encoded}")
    #
    #
    # # Example hexadecimal string
    # b16_string = 'C2E634080810'
    # binary_list = base16_decode_to_binary_list(b16_string)
    # print(f"Binary list: {binary_list}")
