from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI
from typing import Dict, List, Optional
import json
import asyncio
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
import base58
import os

class HarkoAgent:
    def __init__(self, 
                 agent_id: str,
                 openai_api_key: Optional[str] = None,
                 solana_rpc_url: Optional[str] = None):
        """
        Initialize Harko AI Agent
        
        Args:
            agent_id: Unique identifier for the agent
            openai_api_key: OpenAI API key
            solana_rpc_url: Solana RPC URL
        """
        self.agent_id = agent_id
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.solana_client = AsyncClient(solana_rpc_url or "https://api.devnet.solana.com")
        
        # Initialize language model
        self.llm = OpenAI(api_key=self.openai_api_key)
        self.context: List[Dict] = []
        
        # Initialize prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["context", "user_input"],
            template="""
            Context: {context}
            
            User: {user_input}
            
            Assistant: Let me help you with that. 
            """
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
        
    async def process_voice_input(self, 
                                text: str, 
                                session_id: str) -> Dict:
        """
        Process voice input and generate response
        
        Args:
            text: Transcribed voice input
            session_id: Voice session identifier
            
        Returns:
            Dict containing response and metadata
        """
        # Update context
        self.context.append({
            "role": "user",
            "content": text,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Generate response
        response = await self._generate_response(text)
        
        # Store interaction on Solana
        tx_hash = await self._store_interaction(text, response, session_id)
        
        return {
            "response": response,
            "session_id": session_id,
            "tx_hash": tx_hash
        }
        
    async def _generate_response(self, user_input: str) -> str:
        """Generate response using language model"""
        try:
            context_str = json.dumps(self.context[-5:])  # Last 5 interactions
            response = await self.chain.apredict(
                context=context_str,
                user_input=user_input
            )
            
            self.context.append({
                "role": "assistant",
                "content": response,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            return response
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request."
            
    async def _store_interaction(self, 
                               input_text: str, 
                               response: str, 
                               session_id: str) -> str:
        """Store interaction data on Solana blockchain"""
        try:
            # Create transaction (placeholder - implement actual transaction)
            transaction = Transaction()
            # Add instructions for storing voice interaction
            # This is where you'd add your actual Solana program instructions
            
            # Sign and send transaction
            result = await self.solana_client.send_transaction(
                transaction,
                # Add signers here
            )
            
            return base58.b58encode(result["result"]).decode()
            
        except Exception as e:
            print(f"Error storing interaction on Solana: {e}")
            return ""
            
    def get_context(self) -> List[Dict]:
        """Get conversation context"""
        return self.context
        
    async def clear_context(self):
        """Clear conversation context"""
        self.context = []
        
    async def close(self):
        """Cleanup resources"""
        await self.solana_client.close()
