const mapHas = Map.prototype.has;
const mapGet = Map.prototype.get;
const mapSet = Map.prototype.set;

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
