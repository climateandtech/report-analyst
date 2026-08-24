import { Logger  } from "../logger.js";
const logger = new Logger("benchmark");
logger.info("Component connected.");
import { styles } from "../styles/benchmark-styles.js";


class BenchmarkExample extends HTMLElement {

	static observedAttributes = ["select","_schema"]

	// Always constructor and super 
	// Shadow to connect the ShadowDOMTree
	constructor() {
		super();
		this.attachShadow({ mode: "open" })
		this.shadowRoot.adoptedStyleSheets = [styles]
		this.selectedDataset = {}
		this._schema = {}
	}
	
	connectedCallback() {
		logger.info("Custom element added to page.")
		this.changeSelectedDataset()
		window.addEventListener("resize", this.handleResize);
	}

	attributeChangedCallback(name, oldValue, newValue) {
		logger.info(
		`Attribute ${name} has changed from ${oldValue} to ${newValue}.`,
		);
		this.render();
	}	

	disconnectedCallback(){
		logger.info("COMPONENTN IS DISCONNECTED")
		window.removeEventListener("resize", this.handleResize);
	}

	render() {

		const content = this.getAttribute("mode")
		this.shadowRoot.innerHTML = `
            <h1>ABC ${content}</h1>
			<button id="eval-mode">
				Change Mode
			</button>
			<slot name="header"></slot>
			<slot name="content"></slot>
			<slot name="footer"></slot>
			<div id="schema-container"></div>
        `;

		const container = this.shadowRoot.querySelector("#schema-container")
		logger.info("Keys2: ", this._schema)

		if(this._schema.properties){		
			for (const [key, value] of Object.entries(this._schema.properties)) {
				console.log(`${key}: ${value["enum"] ? "select" : value["type"]}`);
				// Creating Selct ui for enum

				// mode
				renderSelect(container, value, key)
				// topK
				renderInteger(container, value, key)
				// MetriksatK
				renderArray(container, value, key)
			}
		}
		const evalMode = this.shadowRoot.querySelector("button#eval-mode")
		logger.info("EVALMODE: ",evalMode)

		// Arrow function to not bind the this context
		evalMode.addEventListener("click", ()=>{
			this.changeMode()
		})
		
	}
	
	changeMode(){
		logger.info("ChangeMODE: ", this.getAttribute("mode"), "TAG: ",this)
		logger.info("Before: ", this.getAttribute("mode"))
		this.setAttribute("mode",this.getAttribute("mode") === "ranking" ? "classification" : "ranking")
		logger.info("After: ", this.getAttribute("mode"))

		const eventChange = new CustomEvent("mode-changes", {
			detail: this.getAttribute("mode"),
		});
		this.dispatchEvent(eventChange)
		
	}

	get mode(){
		return this.getAttribute("mode")
	}

	set mode(x){
		this.setAttribute("mode",x)
	}

	get schema(){
		return this._schema
	}

	set schema(value){
		this._schema = value
		this.render()
	}

	changeSelectedDataset(){
		this.selectedDataset = "10.000.000"
		this.render()
	}

	handleResize() {
		console.log("Window resized");
	}
}

function renderSelect(container, value, key){
	if(!value["enum"]){
		logger.info("Enum return")
		return
	}
	if(value["enum"]){
		// Host for options
		const select = document.createElement("select")
		select.name = key
		for (const content of value.enum){
			const option = document.createElement("option")

			// Options inside Seltion
			option.value = content
			option.textContent = content
			select.appendChild(option)
			// console.log(content)

		}
		container.appendChild(select)
		console.log("HERE IS A SELECT")
	}
}

function renderInteger(container, value, key){
	if(value.type !== "integer"){
		logger.info("Integer return")
		return
	}
	if(value.type === "integer"){
		console.log(`TYPE: ${value}`)
		const input = document.createElement("input") 
		input.name = key
		logger.info("Name: ", key)
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
		container.appendChild(input)
	}
}

function renderArray(container, value, key){
	if(value.type !== "array"){
		logger.info("Array return")
		return
	}
	if(value.type === "array"){
		const div = document.createElement("div") 
		div.id = "id-for-array"
		div.name = key
		const add = document.createElement("button")
		add.id = "add"
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
		
		// document.body.insertBefore(add, document.querySelector("#remove"))
		container.appendChild(div)
		div.querySelector("#add").addEventListener("click", () => {
			const count = div.querySelectorAll(".array-item").length
			if(count < value["maxItems"]){
				tagInput(add, value.items)
				console.log("valuexx: ", div.querySelectorAll(".array-item").length, count, div.querySelectorAll(".array-item").length)
				
			}
			
		})

		function tagInput(where, what){
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
			removeButton.className = "remove-input"
			removeButton.appendChild(document.createTextNode("Remove"))
			insideDiv.appendChild(removeButton)
			insideDiv.querySelector(".remove-input").addEventListener("click", () => {
			// 	console.log("value: ", value["maxItems"])
				
				const count = div.querySelectorAll(".array-item").length
				if(count > value["minItems"]){
					console.log(("AAA; ", div.querySelector(".array-item").childElementCount))
					insideDiv.remove();
				}
				
			})
			// where.appendChild(input)
			div.insertBefore(insideDiv, where)
		}
	}
}

customElements.define("benchmark-example", BenchmarkExample)
