// const testSchema = {
//   "title": "Person",
//   "description": "Person with name and age",
//   "type": "object",
//   "properties": {
//     "name": {
//       "description": "Name of Person",
//       "type": "string",
//       "minLength": 2
//     },
//     "age": {
//       "description": "Age of Person",
//       "type": "integer",
//       "minimum": 0,
//       "maximum": 120
//     },
//     "role": {
//       "description": "Role of Person",
//       "type": "string",
//       "enum": [
//         "student",
//         "employee"
//       ]
//     },
//     "skills": {
//       "type": "array",
//       "minItems": 1,
//       "maxItems": 5,
//       "items": {
//         "type": "string"
//       }
//     },
//     "address": {
//       "type": "object",
//       "description": "Full Address of Person",
//       "properties": {
//         "street": {
//           "type": "string"
//         },
//         "city": {
//           "type": "string"
//         },
//         "zipcode": {
//           "type": "string"
//         }
//       },
//       "required": [
//         "street",
//         "city",
//         "zipcode"
//       ],
//       "additionalProperties": false
//     }
//   },
//   "required": [
//     "name",
//     "age",
//     "role",
//     "skills"
//   ],
//   "additionalProperties": false
// }

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

export default { benchmarkTestSchema};