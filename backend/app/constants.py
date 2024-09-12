import random
import requests


class InstantOffer:
    MAX_RETRY = 5
    VOICE_NOTE_URL = "https://staging-voicebot-demo.marutitech.com/instant-offer-automation-backend"
    VOICE_NOTE_PATH = "static/questions"
    RESPONSE_PATH = "static/user_responses.json"
    AGENT_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    class Prompt:
        #  MAKE_MODEL_YEAR_PROMPT = """
        #  Your task is to validate and extract the data points provided by the user and provide the result strictly in provided JSON format only.
        #  STRICTLY follow the JSON format of {result_json}.
        #  The response provided by the user is related to {question_key}.
        #
        #  Follow these guidelines for extraction of information from the {question_key} and any other datapoint if present in the user response:
        #  1. model_year:
        #  - Extract the model year in YYYY format.
        #  - If the user expresses uncertainty (e.g., "I don't know the year"), add a new key "is_negation": True.
        #  - If you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.
        #
        #  2. make:
        #  - Extract the car manufacturer's name.
        #  - If the user wants to update a make (e.g., "My make is not Toyota, it is Ford"), update the make to the correct one (Ford in this example).
        #  - If the user expresses uncertainty (e.g., "I don't know the make"), add a new key "is_negation": True.
        #  - If you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.
        #  - If the user provides an invalid make that doesn't exist as per your knowledge, add a new key "error_message" with an informative error_message in the final JSON response.
        #  - Always verify whether the present model belongs the given make or not, if not add a new key "error_message" with an informative error_message in the final JSON response.
        #
        #  3. model:
        #  - Extract the car model name.
        #  - If the user wants to update a model, update it appropriately.
        #  - If the user expresses uncertainty (e.g., "I don't know the model"), add a new key "is_negation": True.
        #  - If you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.
        #  - Verify that the provided model should belong to the appropriate result_json['make'], if it is not then add a new key "error_message" with an informative error_message in the final JSON response.
        #
        #  4. postal_code:
        #  - Your task is to extract a 5 digit postal code.
        #  - If the postal code is provided in words (e.g., "two-nine-four-three-one" or "two, nine, four, three, one"), convert it to numerical form (29431 in this example).
        #  - If the postal code is given in an unconventional numeric form, convert it to the numerical form without reducing the original number of digits.
        #  - Ensure the postal code contains only numeric characters.
        #  - If a number, separated by commas, is provided, consider the whole sequence as a valid postal code and don't give an error message.
        #  - If the user expresses uncertainty (e.g., "I don't know the postal code"), add a new key "is_negation": True.
        #  - If the user doesn't provide a 5 digit postal code, add a new key "error_message" with an informative error message in the final JSON.
        #
        #  5. mileage:
        # - Extract the mileage. For any numeric input including the number zero, consider it as a valid and correct mileage and add in the final JSON.
        # - Ensure the mileage contains only numeric characters.
        # - If the mileage is provided in words (e.g., "forty-five thousand miles"), convert it to numerical form (45000 in this example).
        # - If the user expresses uncertainty (e.g., "I don't know the mileage"), add the mileage value "0" in the final JSON.
        # - If the user provides a negative or zero figure mileage, add the mileage value "0" in the final JSON.
        # - If the user provides the mileage as a range, add a new key "error_message" with an informative error_message in the final JSON response.
        # - Don't set the "is_negation" to True, for the mileage datapoint.
        #
        #  Note:
        #  - If the user provides a response in which multiple datapoints are given, out of which some datapoints are correct but some are incorrect, only fill the correctly validated datapoints in the {result_json}. Follow this only when multiple datapoint information is present in the response.
        #  - Strictly Ensure that the format of {result_json} is not changed in the final response.
        #  - If any of the above data points are validated correctly, set "is_negation": False.
        #  - If any data points are not validated and there is negation in the user's response except for the mileage, set "is_negation": True.
        #  - If any data points are not validated and it seems to be an error (not negation), add an "error_message" key in the dictionary with an appropriate comment as the value.
        #  """

        GENERIC_PROMPT = """
        You are an agent for a car selling website who's job is to verify the details provided by the user.
        Your task is to extract the model year, make, and model from the user's response and provide the result strictly in the JSON format as shown below.
        STRICTLY follow the JSON format of result_json: {result_json} and fill the values accordingly.
        Consider the values present in {result_json} while extracting information from user response.
        You need to extract the information regarding the {question_key} only. Hence consider that accordingly for giving error_message.
        
        The current question type is: {question_key}
        Possible values for question_type are: "generic", "year", "make", "model"

        Follow these guidelines:
        
        model_year:
        - Extract the year in YYYY format.
        - If the user provides a year in an abbreviated format (e.g., "04 Chevy Cobalt"), interpret the abbreviated year based on context:
            - For your knowledge, the current year is {current_year}
            - If the abbreviation is a two-digit number between "00" and "99," consider whether it logically refers to a year in the 2000s or 1900s based on the make and model provided (e.g., "04" might be "2004", while "99" might be "1999").
        - If the user expresses uncertainty (e.g., "I don't know the year"), add a new key "is_negation": True.
        - If the question_type is "year" and if you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.
        
        make:
        - Extract the car manufacturer's name or car's make.
        - If the user provides a short form of the make, use your knowledge to convert into an appropriate format (e.g., Chevy -> Chevrolet)
        - If the user expresses uncertainty (e.g., "I don't know the make"), add a new key "is_negation": True.
        - If the question_type is "make" and the if the response is unrelated or incorrect, add a new key "error_message" with an informative error message in the final JSON.
        
        model:
        - Extract the car model name.
        - Verify that the model belongs to the extracted make.
        - If the user expresses uncertainty (e.g., "I don't know the make"), add a new key "is_negation": True.
        - If the question_type is "model" and if you find unrelated response, other than the negation, add a new key "error_message" with an informative error_message in the final JSON response.
        
        *Validation of make-model* :
        - After extracting the make and model, use your knowledge to verify if the combination is valid.
        - If the make-model combination is invalid (e.g., "BMW Mustang" or "Toyota Impala" etc.), add a new key "error_message" with an informative error message in the final JSON.
        - If the make-model combination is invalid, STRICTLY don't try to make it correct, instead add a new key "error_message" with an informative error message in the final JSON. 
        
        Note:
        - Don't give an error_message for missing information unless the question_type specifically asks for that information.
        - If the question_type is "generic", all 3 datapoints (make, model, and year) may or may not be present. Don't give an error_message for missing information in this case.
        - If the question_type is a specific datapoint (year, make, or model), then give an error_message only if that particular datapoint is missing or incorrect.
        
        Analyze the user's response and update the dictionary accordingly.
        {result_json}
        """

        POSTAL_CODE_PROMPT = """
        You are an agent for a car selling website who's job is to verify the details provided by the user.
        Your task is to extract the Postal Code/Zip Code from the user's response and provide the result strictly in the JSON format as shown below.
        STRICTLY follow the JSON format of {result_json}.
        
        Follow these guidelines for extraction of postal_code:
        
        - Your task is to extract a postal code.
        - STRICTLY validate that, if the user provides other than a 5 digit or 9 digit postal code, add a new key "error_message" with an informative error_message in the final JSON.
        - If the user provides a geographic location along with the postal code (e.g., "47345-9775"), only extract and use the first 5 digits of the postal code.
        - If the postal code is provided in words (e.g., "two-nine-four-three-one" or "two, nine, four, three, one"), convert it to numerical form (29431 in this example).
        - If the postal code is given in an unconventional numeric form, convert it to the numerical form without reducing the original number of digits.
        - Ensure the postal code contains only numeric characters.
        - If the user mentions a city name instead of a postal code (e.g., "I don't exactly know, It's in Auburn Hills"), provide the central postal code for that city in the response. Use your knowledge to determine the central postal code for the mentioned city.
        - If a number, separated by commas, is provided, consider the whole sequence as a valid postal code and don't give an error message.
        - If the user expresses complete uncertainty without mentioning any useful information to extract the postal code in the response (e.g., "I don't know the postal code"), add a new key "is_negation": True.
        
        Note:
        - Strictly Ensure that the format of {result_json} is not changed in the final response.
        """

        MILEAGE_PROMPT = """ 
        You are an agent for a car selling website whose job is to verify the details provided by the user.
        Your task is to extract the mileage from the user's response and provide the result strictly in the JSON format as shown below.
        STRICTLY follow the JSON format of {result_json}.
        
        Follow these guidelines for extraction of mileage:
        - Extract the mileage. For any numeric input including the number zero, consider it as a valid and correct mileage and add in the final JSON.
        - Ensure the mileage contains only numeric characters.
        - If the mileage is provided in words (e.g., "forty-five thousand miles"), convert it to numerical form (45000 in this example).
        - If the user expresses uncertainty (e.g., "I don't know the mileage"), add the mileage value "0" in the final JSON.
        - If the user provides a negative or zero figure mileage, add the mileage value "0" in the final JSON.
        - If the user provides the mileage as a range, add a new key "error_message" with an informative error_message in the final JSON response.
        - Don't set the "is_negation" to True, for the mileage datapoint.
        - If the user provides an approximate or uncertain mileage (e.g. "It's 200 and something thousand, I think" or "it's over 200,000" or "roughly 185,000 miles"), extract the numeric value provided and use that as the final mileage. Ignore any qualifiers or uncertainties expressed.
        
        Example responses and their corresponding mileage extractions:
        - "It's 200 and something thousand, I think" -> 200000
        - "it's over 200,000" -> 200000
        - "roughly 185,000 miles" -> 185000
        In these cases, always round to the nearest thousand if necessary and assume the value is in miles.
        
        Note:
        - Strictly Ensure that the format of {result_json} is not changed in the final response.
        """

        RE_ASK_PROMPT = """
        Your task is to determine if the user intends to update existing information. 
        If the user explicitly indicates a desire to update any of the values in the dictionary, set the corresponding value to True. 
        Ensure that only one value in the dictionary is set to True. If the user does not explicitly mention updating any values, set all values in the dictionary to False.

        For example:
        - User says "I want to update the model_year" -> set model_year to True.
        - User says "Update model_year" -> set model_year to True.
        - If the user provides updated value within their update statement (e.g., "I want to update the purchase year to 2020") -> set corresponding key value to False. (here model_year)
        - If the user just mention a year without saying "update" -> set value to False.
        - If the user does not mention updating any values, set all values to False.

        Analyze the user's response and update the dictionary accordingly.

        {result_json}
        """

        DESCRIPTION_PROMPT = """
        Create a concise description of the vehicle based on the provided JSON data. The description should:

        - Clearly mention the vehicle's year, make, and model.
        - Include the mileage of the vehicle.
        - Reference the location using the postal code. If only a postal code is provided, translate it into the corresponding city and state.
        - Use a conversational tone to make the description feel like it's coming from a knowledgeable agent.
        
        Finally, instruct the user:
        "If the details match your vehicle, please press the 'YES' button to confirm. If there’s anything incorrect, press the 'NO' button."
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
        "generic_question": [
            "Could you please provide the year, make, and model of the vehicle you want to sell?",
            "What's the year, make, and model of the car you're putting up for sale?",
            "Please tell me the year, make, and model of the vehicle you're selling.",
            "Can you share the year, make, and model of the car you'd like to sell?",
            "May I have the year, make, and model of the vehicle you're selling?"
        ],
        "model_year": [
            "Can you tell me the model year of your car?",
            "Could you let me know the model year of your vehicle?",
            "Can you provide the year in which your car was manufactured?",
            "Could you share the model year of your car?"
        ],
        "make": [
            "What's the make or company name of your car?",
            "Can you tell me the brand or manufacturer of your car?",
            "Could you provide the make or company name of your car?",
            "What's the brand or company that made your car?",
            "Can you share the name of the company that manufactured your car?"
        ],
        "model": [
            "What's the model of your car?",
            "Can you tell me the model of your car?",
            "Could you provide the model name of your car?",
            "Can you let me know the model of your car?",
            "What is the specific model of your car?"
        ],
        "postal_code": [
            "What's the 5-digit zip code where the vehicle is located?",
            "What's the 5-digit zip code where the car needs to be picked up?",
            "What's your 5-digit postal code?",
            "Can you provide your 5-digit postal code?",
            "Can you let me know your 5-digit zip code?",
        ],
        "mileage": [
            "Whats the miles on your odometer?",
            "What's the current mileage on your vehicle?",
            "Can you tell me the miles shown on the odometer?",
            "What is the mileage on your car's odometer right now?",
            "What is the mileage shown on the odometer?"
        ],

        "successful_terminate": "Based on the information you provided, the estimated value of your car is ${offer_price}. Thank you for using our service!",
        "unsuccessful_terminate": "It seems the information provided is incorrect. Please regenerate the offer and help us in creating a new one with accurate details."
    }

    RESULT_JSON = {
        "model_year": "",
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
        "intermediate_terminate": {
            "path": "",
            "message": ""
        },
        "final_response": {
            "json_description": {
                "path": "",
                "message": ""
            },
            "successful_terminate": {
                "path": "",
                "message": ""
            },
            "unsuccessful_terminate": {
                "path": "",
                "message": ""
            }
        },
        "user_response": "",
        "result_json": "",
        "is_exiting": ""
    }
