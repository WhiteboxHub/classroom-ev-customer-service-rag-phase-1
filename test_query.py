import sys
sys.path.append('/app')
from app.vectorstore.milvus_client import MilvusVectorStore
client = MilvusVectorStore()
try:
    results = client.collection.query(expr='id != ""', output_fields=['diagnostic_category'])
    categories = set([r.get('diagnostic_category') for r in results])
    print('Categories:', categories)
except Exception as e:
    import traceback
    traceback.print_exc()
