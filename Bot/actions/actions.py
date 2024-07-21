# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from typing import Any, Text, Dict, List

import mysql.connector
from datetime import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.executor import CollectingDispatcher


class ActionGenerateStory(Action):

    def name(self) -> Text:
        return "action_generate_story"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot('story_started'):
            dispatcher.utter_message(response="utter_ask_rewrite_story")
            return [SlotSet("rewrite_request", True), SlotSet("story_keeper", tracker.latest_message.get('text'))]

        if tracker.get_slot('story_keeper') != '':
            dispatcher.utter_message(text=tracker.get_slot('story_keeper'))
        else:
            dispatcher.utter_message(response="utter_start")

        return [SlotSet("story_started", True), SlotSet("story_keeper", '')]


class ActionHandleStory(Action):

    def name(self) -> Text:
        return "action_handle_story"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # dispatcher.utter_message(text="Hello World!")
        if not tracker.get_slot('story_started'):
            dispatcher.utter_message(response="utter_prompt_start_story")
            return []

        dispatcher.utter_message(response="utter_continue")

        return [SlotSet("rewrite_request", False)]


class ActionAffirmRewriteStory(Action):
    def name(self):
        return "action_affirm_rewrite_story"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot('rewrite_request'):
            events = [SlotSet("story_started", False), SlotSet("rewrite_request", False)]
            events.append(FollowupAction(name="action_generate_story"))
            #dispatcher.utter_message(text="Alright, let's start a new story. What would you like it to be about?")
            #return [SlotSet("story_started", False), SlotSet("rewrite_request", False)]
            return events
        else:
            dispatcher.utter_message(text="I don't understand your request.")
            return []


class ActionDenyRewriteStory(Action):
    def name(self):
        return "action_deny_rewrite_story"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.get_slot('rewrite_request'):
            dispatcher.utter_message(text="How else can I assist you with your story?")
            return [SlotSet("rewrite_request", False)]
        else:
            dispatcher.utter_message(text="I don't understand your request.")
            return []


class ActionSaveConversation(Action):
    def name(self):
        return "action_save_conversation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if tracker.latest_message.get('intent').get('name') == 'affirm':
            conversation_date = datetime.now().strftime('%Y-%m-%d')
            conversation_text = ''
            for event in tracker.events:
                if event['event'] == "user":
                    conversation_text += 'User:' + event["text"]
                    conversation_text += '\n'
                if event['event'] == 'bot':
                    conversation_text += "Bot:" + event["text"]
                    conversation_text += '\n'
            try:
                connection = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='root',
                    database='rasachatbot'
                )
                my_cursor = connection.cursor()
                sql = "INSERT INTO conversations (conv_date, conv_text) VALUES (%s, %s)"
                val = (conversation_date, conversation_text)
                my_cursor.execute(sql, val)
                connection.commit()
                dispatcher.utter_message(text="Thanks for your cooperation ^._.^")
            except mysql.connector.Error as error:
                dispatcher.utter_message(text=f"Failed to save conversation to database: {error}")
            finally:
                if connection.is_connected():
                    my_cursor.close()
                    connection.close()

        dispatcher.utter_message(text="Have a nice day.")
        return [SlotSet("rewrite_request", False)]
