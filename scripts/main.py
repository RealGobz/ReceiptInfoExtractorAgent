from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.exceptions import OutputParserException
from langchain_ollama import ChatOllama

class InfoExtractor(BaseModel):
    """A class representing the information extracted from a receipt."""
    vendor: str = Field(description="The name of the vendor. e.g., 'Amazon', 'eBay', etc.")
    amount: float = Field(description="the total amount of money spent on the purchase.")
    currency: str = Field(description="the currency in which the amount is denominated, e.g., 'USD', 'SAR', 'EUR', etc.")
    date: Optional[str] = Field(None, description="the date of the purchase in ISO 8601 format (YYYY-MM-DD).")
    category: str = Field(description="the category of the purchase, e.g., 'Electronics', 'Utilities', etc.")

class BatchInfoExtractor(BaseModel):
    """A class representing a batch of information extracted from multiple receipts."""
    receipts: List[InfoExtractor] = Field(description="a list of information extracted from multiple receipts.")


class ReceiptExtractorModel:
    def __init__(self, session_id: str, provider: 'ollama'|'claude' = "ollama", model_id: str = "llama3.1"):
        self.session_id = session_id
        self.store = {} 
        
        # Resolve model mapping to prevent API initialization crashes
        if provider == "claude":
            resolved_model = model_id if "claude" in model_id else "claude-3-5-sonnet-20240620"
            self.llm = ChatAnthropic(model=resolved_model, temperature=0)
        else:
            self.llm = ChatOllama(model=model_id, temperature=0)
            
        self.extractor_llm = self.llm.with_structured_output(BatchInfoExtractor)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a highly disciplined financial auditor. Extract data flawlessly into the requested schema. Do not include any conversational filler."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.extractor_llm
        self.model = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = InMemoryChatMessageHistory()
        return self.store[session_id]

    def flag_discrepancy(self, extracted_batch: BatchInfoExtractor) -> List[dict]:
        """
        Local Python tool that audits the structured data after successful extraction.
        Flags non-compliant records based on business safety logic.
        """
        flags = []
        for index, receipt in enumerate(extracted_batch.receipts):
            # Example business constraint 1: Outrageous transactional limits
            if receipt.amount > 10000:
                flags.append({
                    "receipt_index": index,
                    "field": "amount",
                    "value": receipt.amount,
                    "reason": "Transaction exceeds the maximum single-entry corporate allowance ($10,000)."
                })
            
            # Example business constraint 2: Missing critical audit dates
            if not receipt.date:
                flags.append({
                    "receipt_index": index,
                    "field": "date",
                    "value": None,
                    "reason": "Missing transaction timestamp. Audit trails require valid ISO strings."
                })
        return flags

    def extract_with_recovery(self, raw_text: str, max_retries: int = 3):
        """
        Attempts to extract structured data. Loops back to self-correct if Pydantic
        validation checks throw errors.
        """
        current_input = f"Extract the information from the following text: '{raw_text}'"

        for i in range(1, max_retries + 1):
            try:
                result = self.model.invoke(
                    {"input": current_input},
                    config={"configurable": {"session_id": self.session_id}}
                )
                
                # If extraction succeeds, immediately pass through the local business validation tool
                anomalies = self.flag_discrepancy(result)
                
                return {
                    "status": "success",
                    "data": result.model_dump(),
                    "anomalies_found": anomalies,
                    "attempts_required": i
                }
            
            except (ValidationError, OutputParserException) as e:
                current_input = (
                    f"The previous output failed our strict schema validation with the following error:\n"
                    f"'{str(e)}'\n"
                    f"Analyze the error, match the Pydantic template fields precisely, and regenerate."
                )

            except Exception as e:
                return {"status": "error", "message": f"Critical Backend Failure: {str(e)}"}

        return {
            "status": "failed", 
            "message": f"Maximum self-correction retries ({max_retries}) exhausted without compliance.",
            "last_error": current_input
        }


model = ReceiptExtractorModel(session_id="audit_session_001", provider="ollama", model_id="llama3.1")
result = model.extract_with_recovery(input("Enter the raw text for extraction: "))
print(result)