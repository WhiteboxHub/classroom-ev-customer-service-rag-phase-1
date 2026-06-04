import sys
sys.path.append('/app')
from app.vectorstore.milvus_client import MilvusVectorStore
client = MilvusVectorStore()
try:
    results = client.collection.search(
        data=[[0.1]*384],
        anns_field='embedding',
        param={'metric_type': 'COSINE', 'params': {'ef': 128}},
        limit=10,
        expr='diagnostic_category == "diagnostics"',
        output_fields=[
            'text', 'document_id', 'source_file',
            'vehicle_model', 'vehicle_platform', 'firmware_version',
            'charging_type', 'charging_standard', 'diagnostic_category',
            'dtc_code', 'tenant_id', 'chunk_index', 'page_number',
            'section_hierarchy', 'doc_version'
        ]
    )
    print('Expr Success')
except Exception as e:
    import traceback
    traceback.print_exc()
