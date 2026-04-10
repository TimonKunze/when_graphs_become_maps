import pyperclip

# Prompt to enter url and name
url = input("Please enter url: ")  # Do for part 1 and 2!
PROLIFIC_PID = input("Please enter your name: ")

if url=="pserv":
    url = "http://localhost:8000"  # Do for part 1 and 2!

STUDY_ID = "friendstudy"
SESSION_ID = "nosessionid"

# Create the URL with the actual values
prolificID_url = f"{url}/?PROLIFIC_PID={PROLIFIC_PID}&STUDY_ID={STUDY_ID}&SESSION_ID={SESSION_ID}"

# Copy the URL to the clipboard
pyperclip.copy(prolificID_url)

print("The URL is: ", prolificID_url)
print("The URL has been copied to the clipboard.")
