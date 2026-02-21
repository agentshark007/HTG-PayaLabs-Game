import sys


def remove_blank_lines(input_file):
    try:
        with open(input_file, "r") as f:
            lines = f.readlines()

        # Filter out blank lines
        non_blank_lines = [line for line in lines if line.strip() != ""]

        with open(input_file, "w") as f:
            f.writelines(non_blank_lines)
        print(f"Blank lines removed from {input_file}")

    except FileNotFoundError:
        print(f"Error: The file {input_file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python program.py <file.py>")
    else:
        input_file = sys.argv[1]
        remove_blank_lines(input_file)
