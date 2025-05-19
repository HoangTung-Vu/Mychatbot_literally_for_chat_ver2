"""
Configuration settings for the AI application.
This file centralizes all configuration parameters used across services.
"""

# Chat history and memory configurations
RECENT_MESSAGES_COUNT = 10  # Number of most recent messages to include for context

SIMILAR_DOCUMENTS_THRESHOLD = 0.3  # Threshold for query_similar_documents (higher means more similar)
SIMILAR_DOCUMENTS_COUNT = 6  # Number of similar documents to retrieve


RELEVANT_MESSAGES_THRESHOLD = 0.6  # Threshold for filter_relevant_messages


# Main LLM model configuration
MAIN_LLM_CONFIG = {
    "max_output_tokens": 256,
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 40,
}