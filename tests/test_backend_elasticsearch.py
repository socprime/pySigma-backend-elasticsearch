import pytest
from sigma.backends.elasticsearch import LuceneBackend
from sigma.collection import SigmaCollection

@pytest.fixture
def lucene_backend():
    return LuceneBackend()

def test_lucene_and_expression(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """)

    assert lucene_backend.convert(rule) == ['fieldA:valueA AND fieldB:valueB']

def test_lucene_and_expression_empty_string(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA: valueA
                    fieldB: ''
                condition: sel
        """)

    assert lucene_backend.convert(rule) == ['fieldA:valueA AND fieldB:""']

def test_lucene_or_expression(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel1:
                    fieldA: valueA
                sel2:
                    fieldB: valueB
                condition: 1 of sel*
        """)
    assert lucene_backend.convert(rule) == ['fieldA:valueA OR fieldB:valueB']

def test_lucene_and_or_expression(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA:
                        - valueA1
                        - valueA2
                    fieldB:
                        - valueB1
                        - valueB2
                condition: sel
        """)
    assert lucene_backend.convert(rule) == ['(fieldA:(valueA1 OR valueA2)) AND (fieldB:(valueB1 OR valueB2))']

def test_lucene_or_and_expression(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel1:
                    fieldA: valueA1
                    fieldB: valueB1
                sel2:
                    fieldA: valueA2
                    fieldB: valueB2
                condition: 1 of sel*
        """)
    assert lucene_backend.convert(rule) == ['(fieldA:valueA1 AND fieldB:valueB1) OR (fieldA:valueA2 AND fieldB:valueB2)']

def test_lucene_in_expression(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA:
                        - valueA
                        - valueB
                        - valueC*
                condition: sel
        """)
    assert lucene_backend.convert(rule) == ['fieldA:(valueA OR valueB OR valueC*)']

def test_lucene_in_expression_empty_string(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA:
                        - valueA
                        - ''
                condition: sel
        """)
    assert lucene_backend.convert(rule) == ['fieldA:(valueA OR "")']

def test_lucene_regex_query(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA|re: foo.*bar
                    fieldB: foo
                condition: sel
        """)
    assert lucene_backend.convert(rule) == ['fieldA:/foo.*bar/ AND fieldB:foo']

def test_lucene_regex_query_escaped_input(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA|re: 127\.0\.0\.1:[1-9]\d{3}
                    fieldB: foo
                    fieldC|re: foo/bar
                condition: sel
        """)
    assert lucene_backend.convert(rule) == ['fieldA:/127\.0\.0\.1:[1-9]\d{3}/ AND fieldB:foo AND fieldC:/foo\\/bar/']

def test_lucene_cidr_query(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    field|cidr: 192.168.0.0/16
                condition: sel
        """)
    assert lucene_backend.convert(rule) == ['field:192.168.0.0\\/16']

def test_lucene_field_name_with_whitespace(lucene_backend : LuceneBackend):
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    field name: value
                condition: sel
        """)
    assert lucene_backend.convert(rule) == ['field\\ name:value']

def test_elasticsearch_ndjson_lucene(lucene_backend : LuceneBackend):
    """Test for NDJSON output with embedded query string query."""
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """)
    result = lucene_backend.convert(rule, output_format="kibana_ndjson")
    assert result[0] == {
            "id": "None",
            "type": "search",
            "attributes": {
                "title": "SIGMA - Test",
                "description": None,
                "hits": 0,
                "columns": [],
                "sort": [
                    "@timestamp",
                    "desc"
                ],
                "version": 1,
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": "{\"index\": \"beats-*\", \"filter\": [], \"highlight\": {\"pre_tags\": [\"@kibana-highlighted-field@\"], \"post_tags\": [\"@/kibana-highlighted-field@\"], \"fields\": {\"*\": {}}, \"require_field_match\": false, \"fragment_size\": 2147483647}, \"query\": {\"query_string\": {\"query\": \"fieldA:valueA AND fieldB:valueB\", \"analyze_wildcard\": true}}}"
                    }
                },
                "references": [{
                        "id": "beats-*",
                        "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                        "type": "index-pattern"
                    }]
            }

def test_elasticsearch_siemrule_lucene(lucene_backend : LuceneBackend):
    """Test for NDJSON output with embedded query string query."""
    rule = SigmaCollection.from_yaml("""
            title: Test
            id: c277adc0-f0c4-42e1-af9d-fab062992156
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """)
    result = lucene_backend.convert(rule, output_format="siem_rule")
    assert result[0] == {
            "name":"SIGMA - Test",
            "tags": [],
            "consumer": "siem",
            "enabled": True,
            "throttle": None,
            "schedule":{
                "interval": "5m"
            },
            "params":{
                "author": [],
                "description": "No description",
                "ruleId": "c277adc0-f0c4-42e1-af9d-fab062992156",
                "falsePositives": [],
                "from": "now-5m",
                "immutable": False,
                "license": "DRL",
                "outputIndex": "",
                "meta": {
                    "from": "1m",
                },
                "maxSignals": 100,
                "riskScore": 21,
                "riskScoreMapping": [],
                "severity": "low",
                "severityMapping": [],
                "threat": [],
                "to": "now",
                "references": [],
                "version": 1,
                "exceptionsList": [],
                "relatedIntegrations": [],
                "requiredFields": [],
                "setup": "",
                "type": "query",
                "language": "lucene",
                "index": [
                    "apm-*-transaction*",
                    "auditbeat-*",
                    "endgame-*",
                    "filebeat-*",
                    "logs-*",
                    "packetbeat-*",
                    "traces-apm*",
                    "winlogbeat-*",
                    "-*elastic-cloud-logs-*"
                ],
                "query": "fieldA:valueA AND fieldB:valueB",
                "filters": []
            },
            "rule_type_id":"siem.queryRule",
            "notify_when":"onActiveAlert",
            "actions":[]
            }

def test_elasticsearch_siemrule_lucene_ndjson(lucene_backend : LuceneBackend):
    """Test for NDJSON output with embedded query string query."""
    rule = SigmaCollection.from_yaml("""
            title: Test
            id: c277adc0-f0c4-42e1-af9d-fab062992156
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """)
    result = lucene_backend.convert(rule, output_format="siem_rule_ndjson")
    assert result[0] == {
            "id": "c277adc0-f0c4-42e1-af9d-fab062992156",
            "name":"SIGMA - Test",
            "tags": [],
            "interval": "5m",
            "enabled": True,
            "description": "No description",
            "risk_score": 21,
            "severity": "low",
            "license": "DRL",
            "output_index": "",
            "meta": {
                "from": "1m",
            },
            "author": [],
            "false_positives": [],
            "from": "now-5m",
            "rule_id": "c277adc0-f0c4-42e1-af9d-fab062992156",
            "max_signals": 100,
            "risk_score_mapping": [],
            "severity_mapping": [],
            "threat": [],
            "to": "now",
            "references": [],
            "version": 1,
            "exceptions_list": [],
            "immutable": False,
            "related_integrations": [],
            "required_fields": [],
            "setup": "",
            "type": "query",
            "language": "lucene",
            "index": [
                "apm-*-transaction*",
                "auditbeat-*",
                "endgame-*",
                "filebeat-*",
                "logs-*",
                "packetbeat-*",
                "traces-apm*",
                "winlogbeat-*",
                "-*elastic-cloud-logs-*"
            ],
            "query": "fieldA:valueA AND fieldB:valueB",
            "filters": [],
            "throttle": "no_actions",
            "actions":[]
            }

def test_elasticsearch_dsl_lucene(lucene_backend : LuceneBackend):
    """Test for DSL output with embedded query string query."""
    rule = SigmaCollection.from_yaml("""
            title: Test
            status: test
            logsource:
                category: test_category
                product: test_product
            detection:
                sel:
                    fieldA: valueA
                    fieldB: valueB
                condition: sel
        """)
    assert lucene_backend.convert(rule, output_format="dsl_lucene") == [{
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "fieldA:valueA AND fieldB:valueB",
                            "analyze_wildcard": True
                        }
                    }
                ]
            }
        }
    }]

def test_elasticsearch_kibana_output(lucene_backend : LuceneBackend):
    """Test for output format kibana."""
    # TODO: implement a test for the output format
    pass

def test_elasticsearch_siem_rule_output(lucene_backend : LuceneBackend):
    """Test for output format siem_rule."""
    # TODO: implement a test for the output format
    pass

def test_elasticsearch_siem_rule_ndjson_output(lucene_backend : LuceneBackend):
    """Test for output format siem_rule."""
    # TODO: implement a test for the output format
    pass