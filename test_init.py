# File: test_main.py


if __name__ == "__main__":
    while True:
        message = input("Enter a message (or 'exit' to quit): ")
        if message.lower() == "exit":
            print("Exiting the program.")
            break
        else:
            print(f"You entered: {message}")
