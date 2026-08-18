import { Logger  } from "../logger.js";
const logger = new Logger("benchmark");
logger.info("Component connected.");
import { styles } from "../styles/benchmark-styles.js";


class BenchmarkExample extends HTMLElement {

	static observedAttributes = ["mode"]

	// Always constructor and super 
	// Shadow to connect the ShadowDOMTree
	constructor() {
		super();
		this.attachShadow({ mode: "open" })
		this.shadowRoot.adoptedStyleSheets = [styles]
		this.selectedDataset = null
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
			<div>${this.selectedDataset}</div>
        `;
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

	changeSelectedDataset(){
		this.selectedDataset = "10.000.000"
		this.render()
	}

	handleResize() {
		console.log("Window resized");
	}
}

customElements.define("benchmark-example", BenchmarkExample)
