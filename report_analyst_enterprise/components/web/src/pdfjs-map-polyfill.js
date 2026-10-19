// pdf.js 6 calls JS methods that Electron 34 does not provide yet.
const mapHas = Map.prototype.has;
const mapGet = Map.prototype.get;
const mapSet = Map.prototype.set;
const hexAlphabet = "0123456789abcdef";

if (typeof Map.prototype.getOrInsert !== "function") {
  Object.defineProperty(Map.prototype, "getOrInsert", {
    configurable: true,
    writable: true,
    value(key, value) {
      if (mapHas.call(this, key)) return mapGet.call(this, key);

      mapSet.call(this, key, value);
      return value;
    },
  });
}

if (typeof Map.prototype.getOrInsertComputed !== "function") {
  Object.defineProperty(Map.prototype, "getOrInsertComputed", {
    configurable: true,
    writable: true,
    value(key, callback) {
      if (typeof callback !== "function") {
        throw new TypeError("Map.getOrInsertComputed callback must be a function");
      }
      if (mapHas.call(this, key)) return mapGet.call(this, key);

      const value = callback(key);
      mapSet.call(this, key, value);
      return value;
    },
  });
}

if (typeof Uint8Array.prototype.toHex !== "function") {
  Object.defineProperty(Uint8Array.prototype, "toHex", {
    configurable: true,
    writable: true,
    value() {
      const bytes = new Uint8Array(this.buffer, this.byteOffset, this.byteLength);
      let hex = "";
      for (let index = 0; index < bytes.length; index += 1) {
        const byte = bytes[index];
        hex += hexAlphabet[byte >> 4] + hexAlphabet[byte & 0x0f];
      }
      return hex;
    },
  });
}

if (typeof Uint8Array.prototype.toBase64 !== "function") {
  Object.defineProperty(Uint8Array.prototype, "toBase64", {
    configurable: true,
    writable: true,
    value() {
      const bytes = new Uint8Array(this.buffer, this.byteOffset, this.byteLength);
      let binary = "";
      for (let index = 0; index < bytes.length; index += 1) {
        binary += String.fromCharCode(bytes[index]);
      }
      return btoa(binary);
    },
  });
}

if (typeof Uint8Array.fromBase64 !== "function") {
  Object.defineProperty(Uint8Array, "fromBase64", {
    configurable: true,
    writable: true,
    value(encoded) {
      const binary = atob(String(encoded).replace(/[\t\n\f\r ]/g, ""));
      const bytes = new Uint8Array(binary.length);
      for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
      }
      return bytes;
    },
  });
}
