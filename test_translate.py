import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import AzureOpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

# === GENERAL CONFIGURATIONS ===
client = AzureOpenAI(
    api_key=os.getenv('AZURE_ASSISTANT_API_KEY'),
    api_version=os.getenv('AZURE_ASSISTANT_API_VERSION'),
    azure_endpoint=os.getenv('AZURE_ASSISTANT_DOMAIN'),
    azure_deployment=os.getenv('AZURE_ASSISTANT_DEPLOYMENT_ID')
)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index(os.getenv('PINECONE_INDEX_NAME'))


# === RETRIEVAL FUNCTION ===
def retrieve_similar_sentence(query_sentence):
    query_embedding = model.encode(query_sentence).tolist()

    response = index.query(
        vector=query_embedding,
        top_k=4,
        include_metadata=True
    )
    
    results = []
    for match in response['matches']:
      metadata = match['metadata']
      score = match['score']

      results.append({
          "source_sentence": metadata["source_sentence"],
          "target_sentence": metadata["target_sentence"],
          "score": score
      })
    
    return results


# === TRANSLATION FUNCTION ===
def translate_sentence(sentence, source_language="english", target_language="quechua"):
    results = retrieve_similar_sentence(sentence)

    prompt = f""" Your task is to translate text from source_language 
                {source_language} to target_language {target_language} 
                using provided context details.

                context:
                ```
                source_sentence: {results[0]["source_sentence"]}
                target_sentence: {results[0]["target_sentence"]}

                source_sentence: {results[1]["source_sentence"]}
                target_sentence: {results[1]["target_sentence"]}

                source_sentence: {results[2]["source_sentence"]}
                target_sentence: {results[2]["target_sentence"]}

                source_sentence: {results[3]["source_sentence"]}
                target_sentence: {results[3]["target_sentence"]}
                ```

                text:
                ```
                {sentence}
                ```
    """

    response = client.chat.completions.create(
        model="gpt4-o",
        messages=[{"role": "system", "content": prompt},
                    {"role": "user", "content": sentence}]
    )

    return response.choices[0].message.content


# === MAIN ===
answer = "Open your mouth. Now take off your clothes, I'm going to examine you"
translation = translate_sentence(answer)
print(f"\n{translation}")