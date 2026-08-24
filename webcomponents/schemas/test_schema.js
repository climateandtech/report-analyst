const benchmarkTestSchema = {
  "title": "BenchmarkConfig",
  "description": "Configuration template for benchmark",
  "type": "object",
  "properties": {
    "mode": {
      "type": "string",
      "enum": [
        "ranking",
        "classification"
      ]
    },
    "topK": {
      "description": "",
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 10
    },
    "metricsAtK": {
      "description": "",
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "items": {
        "type": "integer",
        "minimum": 1
      }
    }
  },
  "required": [
    "mode",
    "topK",
    "metricsAtK"
  ],
  "additionalProperties": false
}

export default benchmarkTestSchema;