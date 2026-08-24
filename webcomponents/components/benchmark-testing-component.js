import { Logger  } from "../logger.js"
const logger = new Logger("benchmark")
logger.info("Component connected.")
import { styles } from "../styles/benchmark-styles.js"


class BenchmarkSchema extends HTMLElement {

	// Always constructor and super 
	// Shadow to connect the ShadowDOMTree
	constructor() {
		super()
		this.attachShadow({ mode: "open" })
		this.shadowRoot.adoptedStyleSheets = [styles]
		this._schema = {}
		this._formData = {}
	}
	
	connectedCallback() {
		logger.info("Custom element added to page.")
	}

	disconnectedCallback(){
		logger.info("COMPONENTN IS DISCONNECTED")
	}

	render() {
		this.shadowRoot.innerHTML = `
            
			<div id="schema-container"></div>
        `

		const container = this.shadowRoot.querySelector("#schema-container")
		logger.info("SCHEMA: ", this._schema)
		const form = document.createElement("form")

		let labelTitel = null
			if(this._schema.title) {
				labelTitel = this._schema.title
				const label = document.createElement("label")
				logger.info("LABEL: ",)
				let h = document.createElement("h2")
				h.textContent = "Label"
				label.appendChild(h)
				form.className = "form-schema"
				form.appendChild(label)
			}

		if(this._schema.properties){		1
			for (const [key, fieldType] of Object.entries(this._schema.properties)) {
				logger.info("Label: ", this._schema.title)

				const wrapper = fieldType.type !== "array" ? document.createElement("div") : document.createElement("fieldset")
				const label = fieldType.type !== "array" ? document.createElement("label") : document.createElement("legend")

				label.htmlFor = key
				label.textContent = fieldType.title ?? key

				wrapper.appendChild(label)

				// Creating Selct ui for enum
				// mode
				if(fieldType["enum"]) renderSelect(wrapper,fieldType, key, (changedKey, changedValue) => {this.updateFormData(changedKey, changedValue)})
				// topK
				if(fieldType.type === "integer") renderInteger(wrapper, fieldType, key, (changedKey, changedValue) => {this.updateFormData(changedKey, changedValue)})
				// MetriksatK
				if(fieldType.type === "array") renderArray(wrapper, fieldType, key, (changedKey, changedValue) => {this.updateFormData(changedKey, changedValue)})

				form.appendChild(wrapper)
			}
		}
		container.appendChild(form)
	}
	
	get schema(){
		return this._schema
	}

	set schema(value){
		this._schema = value
		this.render()
	}

	get formData(){
		return this._formData
	}

	updateFormData(key, value){
		this._formData[key] = value
		logger.info("FORM DATA:", this._formData)
	}

	get formData() {
		return this._formData
	}

	set formData(value) {
		this._formData = value
		this.render()
	}
}

function renderSelect(wrapper, value, key, refreshCallback){
	if(!value["enum"]){
		logger.info("Enum return")
		return
	}

	// Host for options
	const select = document.createElement("select")
	select.name = key
	select.id = key
	for (const content of value.enum){
		const option = document.createElement("option")
		// const option = document.createTextNode(content)
		// options.appendChild(option)

		// Options inside Seltion
		option.value = content
		option.textContent = content
		select.appendChild(option)
		// console.log(content)

	}
	wrapper.appendChild(select)
	console.log("HERE IS A SELECT")

	select.addEventListener('change', (event) => {

		// this._formData[key] = neuerWert
		const selectedValue = event.target.value
		logger.info('Selected value:', selectedValue)
		refreshCallback(key, selectedValue)
	})

}

function renderInteger(wrapper, value, key, refreshCallback){
	if(value.type !== "integer"){
		logger.info("Integer return")
		return
	}
	// console.log(`TYPE: ${value}`)
	const input = document.createElement("input") 
	input.name = key
	input.id = key
	for(const content of Object.entries(value)){
		// console.log(content[0])
		if(content[0] === "type"){
			input.type = "number"
		}else if(content[0] === "minimum"){
			input.min = content[1]
		}else if(content[0] === "maximum"){
			input.max = content[1]
		}else if(content[0] === "default"){
			input.defaultValue = content[1]
		}
	}
	wrapper.appendChild(input)

	input.addEventListener('change', (event) => {

		// this._formData[key] = neuerWert
		const selectedValue = event.target.valueAsNumber
		logger.info('Selected value:', selectedValue)
		refreshCallback(key, selectedValue)
	})
}

function renderArray(wrapper, value, key, refreshCallback){
	if(value.type !== "array"){
		logger.info("Array return")
		return
	}

	const div = document.createElement("div") 
	div.className = "array-field"
	div.name = key
	const add = document.createElement("button")
	add.id = "add"
	add.type = "button"
	add.appendChild(document.createTextNode("Add"))

	div.appendChild(add)

	for(let content of Object.entries(value)){
		// console.log("ITEMS: ",content[0])
		if(content[0] === "type"){
			div.type = "number"
		}else if(content[0] === "minItems"){
			div.min = content[1]
		}else if(content[0] === "maxItems"){
			div.max = content[1]
		}
	}
	
	console.log(value["minItems"])
	for (let index = 0; index < value["minItems"]; index++) {
		if(value.items){
			tagInput(add, value.items)
		}
	}
	logger.info("ARRAY: ", div.querySelectorAll(".array-item"))

	// document.body.insertBefore(add, document.querySelector("#remove"))
	wrapper.appendChild(div)

	div.querySelector("#add").addEventListener("click", () => {
		const count = div.querySelectorAll(".array-item").length
		if(count < value["maxItems"]){
			tagInput(add, value.items)
			console.log("valuexx: ", div.querySelectorAll(".array-item").length, count, div.querySelectorAll(".array-item").length)
		}

	})

	div.addEventListener('change', (event) => {

		// this._formData[key] = neuerWert
		const selectedValue = collectArrayValues()
		logger.info('Selected value:', selectedValue)
		refreshCallback(key, selectedValue)
	})


	function collectArrayValues(){
		const items = Array.from(div.querySelectorAll(".array-item"))
		const values = items.map(item => {
			const input = item.querySelector("input")
			return Number(input.value)
		})
		return values

	}

	function tagInput(where, what){
		const selectedValue = collectArrayValues()
		refreshCallback(key, selectedValue)
		let insideDiv = document.createElement("div")
		const input = document.createElement("input")
			for(let content of Object.entries(what)){
				// console.log("INSIDE: ", content)
				
				if(content[0] === "type"){
					input.type = "number"
				}else if(content[0] === "minimum"){
					input.min = content[1]
				}
			}
		insideDiv.appendChild(input)
		insideDiv.className = "array-item"
		let removeButton = document.createElement("button")
		removeButton.type = "button"
		removeButton.className = "remove-input"
		removeButton.appendChild(document.createTextNode("Remove"))
		insideDiv.appendChild(removeButton)
		insideDiv.querySelector(".remove-input").addEventListener("click", () => {
		// 	console.log("value: ", value["maxItems"])
			
			const count = div.querySelectorAll(".array-item").length
			if(count > value["minItems"]){
				console.log(("AAA: ", div.querySelector(".array-item").childElementCount))
				insideDiv.remove()
				const selectedValue = collectArrayValues()
				refreshCallback(key, selectedValue)
			}
			
		})
		// where.appendChild(input)
		div.insertBefore(insideDiv, where)
		
	}
}

customElements.define("benchmark-schema", BenchmarkSchema)
