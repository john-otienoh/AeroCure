import africastalking
import os

from dotenv import load_dotenv


load_dotenv()

africastalking.initialize(
		username="EMID",
		api_key=os.getenv("AT_API_KEY")

	)


sms = africastalking.SMS


def welcome_message(phone_number, message):
	recipients = [f"+254{str(phone_number)}"]

	# message = ;

	sender = 20880

	try:
		response = sms.send(message, recipients, sender)

		print(response)

	except Exception as e:
		print(f'Houston! we have a problem: {e}')



get_phone_number = int(input("Enter phone number: "))
get_user_message = input("Enter the message: ")

welcome_message(get_phone_number, get_user_message)