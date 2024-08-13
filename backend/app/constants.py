import random
import requests


class InstantOffer:
    MAX_RETRY = 5
    VOICE_NOTE_URL = "https://f437-61-12-85-170.ngrok-free.app"
    VOICE_NOTE_PATH = "static/questions"
    RESPONSE_PATH = "static/user_responses.json"
    AGENT_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    OFFER_PRICES = [1800, 1950, 2000, 2050, 2100, 2350, 2400, 2450, 2500, 2590, 2700, 2750, 2900, 2910, 3000]

    class Prompt:
        GENERIC_PROMPT = """
        Your task is to validate and extract the data points provided by the user and provide the result strictly in provided JSON format only.
        STRICTLY follow the JSON format of {result_json}.
        The response provided by the user is related to {question_key}.

        Note that the current year is {current_year}.

        Follow these guidelines for extraction of information from the {question_key} and any other datapoint if present in the user response:
        1. purchase_year:
        - Extract the year in YYYY format.
        - If the user expresses uncertainty (e.g., "I don't know the year"), add a new key "is_negation": True.
        - If you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.        

        2. make:
        - Extract the car manufacturer's name.
        - If the user wants to update a make (e.g., "My make is not Toyota, it is Ford"), update the make to the correct one (Ford in this example).
        - If the user expresses uncertainty (e.g., "I don't know the make"), add a new key "is_negation": True.
        - If you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.
        - If the user provides an invalid make that doesn't exist as per your knowledge, add a new key "error_message" with an informative error_message in the final JSON response.
        - Always verify whether the present model belongs the given make or not, if not add a new key "error_message" with an informative error_message in the final JSON response.

        3. model:
        - Extract the car model name.
        - If the user wants to update a model, update it appropriately.
        - If the user expresses uncertainty (e.g., "I don't know the model"), add a new key "is_negation": True.
        - If you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.
        - Verify that the provided model should belong to the appropriate make, if it is not then add a new key "error_message" with an informative error_message in the final JSON response.

        4. postal_code:
        - Your task is to extract a 5 digit postal code.
        - If the postal code is provided in words (e.g., "two-nine-four-three-one" or "two, nine, four, three, one"), convert it to numerical form (29431 in this example).
        - If the postal code is given in an unconventional numeric form, convert it to the numerical form without reducing the original number of digits.
        - Ensure the postal code contains only numeric characters.
        - If a number, separated by commas, is provided, consider the whole sequence as a valid postal code and don't give an error message.
        - If the user expresses uncertainty (e.g., "I don't know the postal code"), add a new key "is_negation": True.
        - If the user doesn't provide a 5 digit postal code, add a new key "error_message" with an informative error message in the final JSON.

        5. mileage:
       - Extract the mileage. For any numeric input including the number zero, consider it as a valid and correct mileage and add in the final JSON.
       - Ensure the mileage contains only numeric characters.
       - If the mileage is provided in words (e.g., "forty-five thousand miles"), convert it to numerical form (45000 in this example).
       - If the user expresses uncertainty (e.g., "I don't know the mileage"), add the mileage value "0" in the final JSON.
       - If the user provides a negative or zero figure mileage, add the mileage value "0" in the final JSON.
       - If the user provides the mileage as a range, add a new key "error_message" with an informative error_message in the final JSON response.
       - Don't set the "is_negation" to True, for the mileage datapoint.

        Note:
        - If the user provides a response in which multiple datapoints are given, out of which some datapoints are correct but some are incorrect, only fill the correctly validated datapoints in the {result_json}. Follow this only when multiple datapoint information is present in the response.
        - Strictly Ensure that the format of {result_json} is not changed in the final response.
        - If any of the above data points are validated correctly, set "is_negation": False.
        - If any data points are not validated and there is negation in the user's response except for the mileage, set "is_negation": True.
        - If any data points are not validated and it seems to be an error (not negation), add an "error_message" key in the dictionary with an appropriate comment as the value.
        """

        RE_ASK_PROMPT = """
        Your task is to determine if the user intends to update existing information. 
        If the user explicitly indicates a desire to update any of the values in the dictionary, set the corresponding value to True. 
        Ensure that only one value in the dictionary is set to True. If the user does not explicitly mention updating any values, set all values in the dictionary to False.

        For example:
        - User says "I want to update the purchase_year" -> set purchase_year to True.
        - User says "Update purchase_year" -> set purchase_year to True.
        - If the user provides updated value within their update statement (e.g., "I want to update the purchase year to 2020") -> set corresponding key value to False. (here purchase_year)
        - If the user just mention a year without saying "update" -> set value to False.
        - If the user does not mention updating any values, set all values to False.

        Analyze the user's response and update the dictionary accordingly.

        {result_json}
        """

    class Messages:
        INITIAL = [
            "Hi there! I'm here to help you get an instant offer for your car by asking you a few quick questions.",
            "Hi! I'm here to assist you in getting an instant offer for your car by asking a few quick questions.",
            "Hello! I'll help you get an instant offer for your car by asking you some quick questions.",
            "Hi! Let me assist you in getting an instant offer for your car by asking some quick questions.",
            "Hi! I can help you get an instant offer for your car by asking a few quick questions."]
        WAITING = "Thanks for your patience! Please wait a moment."
        RETRY_MESSAGE = "Failed to collect audio data for {question_key}"
        RE_ASK_MESSAGE = "Okay, Can you also provide the information about the {question_key}!"
        MAX_RETRY_MESSAGE = "Max retries reached for {question_key}. Exiting."
        FAILED_TO_COLLECT_AUDIO_MESSAGE = "Failed to collect audio data for {question_key} after {max_retries} retries."
        INTERMEDIATE_TERMINATE = "Thanks for contacting us. All data points are mandatory. We'll be happy to assist you once we have all the details!"

    QUESTIONS = {
        "generic_question": ["Can you please provide the details of your vehicle?",
                             "Could you provide me the information about your vehicle?",
                             "Would you please share the details about your vehicle?",
                             "Can you tell me the details regarding your vehicle?",
                             "Can you share the information regarding your vehicle?"],

        "purchase_year": ["Can you tell me the year you bought your car?",
                          "Could you let me know the year you purchased your car?",
                          "Can you provide the year in which you bought your car?",
                          "Could you share the year you bought your car?"],

        "make": ["What's the make or company name of your car?",
                 "Can you tell me the brand or manufacturer of your car?",
                 "Could you provide the make or company name of your car?",
                 "What's the brand or company that made your car?",
                 "Can you share the name of the company that manufactured your car?"],

        "model": ["What's the model of your car?",
                  "Can you tell me the model of your car?",
                  "Could you provide the model name of your car?",
                  "Can you let me know the model of your car?",
                  "What is the specific model of your car?"],

        "postal_code": ["What's your 5-digit postal code?",
                        "Can you provide your 5-digit postal code?",
                        "Can you let me know your 5-digit zip code?",
                        "Could you tell me your 5-digit zip code?"],

        "mileage": ["What's the mileage on your car?",
                    "Can you tell me the mileage on your car?",
                    "Could you provide the mileage of your car?",
                    "What is the current mileage on your car?",
                    "Can you let me know how many miles your car has?"],

        "successful_terminate": f"Based on the information you provided, the estimated value of your car is ${random.choice(OFFER_PRICES)}. Thank you for using our service!"
    }

    RESULT_JSON = {
        "purchase_year": "",
        "make": "",
        "model": "",
        "postal_code": "",
        "mileage": ""
    }

    BROADCAST_MESSAGE = {
        "initial_message_path": "",
        "question": {
            "path": "",
            "text": ""
        },
        "error": {
            "path": "",
            "message": ""
        },
        "terminate": {
            "path": "",
            "message": ""
        },
        "user_response": "",
        "result_json": "",
        "is_exiting": ""
    }
