from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .analyzers import ngram_analyzer
from .models import Product


@registry.register_document
class ProductDocument(Document):
    # define class variables if you wanna give custom mappings or you need to include fields like ForeignKeyField or ManyToManyField etc.
    # For ForeignKeyField use ObjectField
    # For ManyToManyField use NestedField

    # Make sure to name the variable same as the field name in the Product Model and also make sure to provide all fields in the related model i.e. Category here must have all fields as well as id field
    
    # Your Final document will look like this
    # {
    #     "name": "<>",
    #     "final_price": "<>",
    #     "on_sale": "<>",
    #     "average_rating": "<>",
    #     "category": {
    #         "name": "<>",
    #         "id": 1
    #     }
    # }
    category = fields.ObjectField(
        properties = {
            'id': fields.IntegerField(),
            'name': fields.TextField(
                analyzer = ngram_analyzer,
                fields = {
                    'raw': fields.KeywordField() # allows doing partial as well as EXACT matching. FOR Partial matches -> ProductDocument.search().query("match", category.name=search_query) FOR EXACT matches -> filter.term(category.name.raw="Smartphones")
                }
            ),
        }
    )

    # Give custom mappings to all fields ow ES will use all fields as TextField
    name = fields.TextField(analyzer = ngram_analyzer)
    final_price = fields.FloatField()
    on_sale = fields.BooleanField()
    average_rating = fields.FloatField()

    # Autocomplete stuff
    name_suggest = fields.CompletionField()
    category_suggest = fields.CompletionField()

    class Index:
        name = 'products' # ES index name

    # Django Inner class connects the Elasticsearch document to the model in this case Product and controls what all fields are going to be indexed.
    # fields: Lists additional model fields to include in the Elasticsearch document without explicitly defining them as class variables.
    class Django:
        model = Product
        fields = []

    def get_queryset(self):
        """Not mandatory but to improve performance we can select related in one sql request"""
        return super().get_queryset().select_related(
            'category'
        )
    
    # Prepare Fields
    def prepare_final_price(self, instance):
        return instance.sale_price if instance.on_sale else instance.price
    
    
    def prepare_name_suggest(self, instance):
        return {
            'input': [instance.name],
            'weight': 5 # higher priority in autocomplete suggestions
        }
    

    def prepare_category_suggest(self, instance):
        return {
            'input': [instance.category.name],
            'weight': 3 # lower priority in autocomplete suggestions
        }