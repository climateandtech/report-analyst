var a1 = Object.defineProperty;
var l1 = (e, t, i) => t in e ? a1(e, t, { enumerable: !0, configurable: !0, writable: !0, value: i }) : e[t] = i;
var bt = (e, t, i) => l1(e, typeof t != "symbol" ? t + "" : t, i);
function zs(e) {
  return e && e.__esModule && Object.prototype.hasOwnProperty.call(e, "default") ? e.default : e;
}
var fv = { exports: {} }, Ie = {};
/**
 * @license React
 * react.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var fy;
function u1() {
  if (fy) return Ie;
  fy = 1;
  var e = Symbol.for("react.element"), t = Symbol.for("react.portal"), i = Symbol.for("react.fragment"), o = Symbol.for("react.strict_mode"), a = Symbol.for("react.profiler"), l = Symbol.for("react.provider"), c = Symbol.for("react.context"), f = Symbol.for("react.forward_ref"), d = Symbol.for("react.suspense"), m = Symbol.for("react.memo"), y = Symbol.for("react.lazy"), h = Symbol.iterator;
  function S(P) {
    return P === null || typeof P != "object" ? null : (P = h && P[h] || P["@@iterator"], typeof P == "function" ? P : null);
  }
  var $ = { isMounted: function() {
    return !1;
  }, enqueueForceUpdate: function() {
  }, enqueueReplaceState: function() {
  }, enqueueSetState: function() {
  } }, v = Object.assign, w = {};
  function _(P, b, R) {
    this.props = P, this.context = b, this.refs = w, this.updater = R || $;
  }
  _.prototype.isReactComponent = {}, _.prototype.setState = function(P, b) {
    if (typeof P != "object" && typeof P != "function" && P != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
    this.updater.enqueueSetState(this, P, b, "setState");
  }, _.prototype.forceUpdate = function(P) {
    this.updater.enqueueForceUpdate(this, P, "forceUpdate");
  };
  function E() {
  }
  E.prototype = _.prototype;
  function k(P, b, R) {
    this.props = P, this.context = b, this.refs = w, this.updater = R || $;
  }
  var j = k.prototype = new E();
  j.constructor = k, v(j, _.prototype), j.isPureReactComponent = !0;
  var T = Array.isArray, N = Object.prototype.hasOwnProperty, x = { current: null }, F = { key: !0, ref: !0, __self: !0, __source: !0 };
  function V(P, b, R) {
    var C, I = {}, B = null, X = null;
    if (b != null) for (C in b.ref !== void 0 && (X = b.ref), b.key !== void 0 && (B = "" + b.key), b) N.call(b, C) && !F.hasOwnProperty(C) && (I[C] = b[C]);
    var J = arguments.length - 2;
    if (J === 1) I.children = R;
    else if (1 < J) {
      for (var se = Array(J), ce = 0; ce < J; ce++) se[ce] = arguments[ce + 2];
      I.children = se;
    }
    if (P && P.defaultProps) for (C in J = P.defaultProps, J) I[C] === void 0 && (I[C] = J[C]);
    return { $$typeof: e, type: P, key: B, ref: X, props: I, _owner: x.current };
  }
  function U(P, b) {
    return { $$typeof: e, type: P.type, key: b, ref: P.ref, props: P.props, _owner: P._owner };
  }
  function G(P) {
    return typeof P == "object" && P !== null && P.$$typeof === e;
  }
  function Q(P) {
    var b = { "=": "=0", ":": "=2" };
    return "$" + P.replace(/[=:]/g, function(R) {
      return b[R];
    });
  }
  var H = /\/+/g;
  function q(P, b) {
    return typeof P == "object" && P !== null && P.key != null ? Q("" + P.key) : b.toString(36);
  }
  function le(P, b, R, C, I) {
    var B = typeof P;
    (B === "undefined" || B === "boolean") && (P = null);
    var X = !1;
    if (P === null) X = !0;
    else switch (B) {
      case "string":
      case "number":
        X = !0;
        break;
      case "object":
        switch (P.$$typeof) {
          case e:
          case t:
            X = !0;
        }
    }
    if (X) return X = P, I = I(X), P = C === "" ? "." + q(X, 0) : C, T(I) ? (R = "", P != null && (R = P.replace(H, "$&/") + "/"), le(I, b, R, "", function(ce) {
      return ce;
    })) : I != null && (G(I) && (I = U(I, R + (!I.key || X && X.key === I.key ? "" : ("" + I.key).replace(H, "$&/") + "/") + P)), b.push(I)), 1;
    if (X = 0, C = C === "" ? "." : C + ":", T(P)) for (var J = 0; J < P.length; J++) {
      B = P[J];
      var se = C + q(B, J);
      X += le(B, b, R, se, I);
    }
    else if (se = S(P), typeof se == "function") for (P = se.call(P), J = 0; !(B = P.next()).done; ) B = B.value, se = C + q(B, J++), X += le(B, b, R, se, I);
    else if (B === "object") throw b = String(P), Error("Objects are not valid as a React child (found: " + (b === "[object Object]" ? "object with keys {" + Object.keys(P).join(", ") + "}" : b) + "). If you meant to render a collection of children, use an array instead.");
    return X;
  }
  function ie(P, b, R) {
    if (P == null) return P;
    var C = [], I = 0;
    return le(P, C, "", "", function(B) {
      return b.call(R, B, I++);
    }), C;
  }
  function ne(P) {
    if (P._status === -1) {
      var b = P._result;
      b = b(), b.then(function(R) {
        (P._status === 0 || P._status === -1) && (P._status = 1, P._result = R);
      }, function(R) {
        (P._status === 0 || P._status === -1) && (P._status = 2, P._result = R);
      }), P._status === -1 && (P._status = 0, P._result = b);
    }
    if (P._status === 1) return P._result.default;
    throw P._result;
  }
  var pe = { current: null }, Z = { transition: null }, ae = { ReactCurrentDispatcher: pe, ReactCurrentBatchConfig: Z, ReactCurrentOwner: x };
  function z() {
    throw Error("act(...) is not supported in production builds of React.");
  }
  return Ie.Children = { map: ie, forEach: function(P, b, R) {
    ie(P, function() {
      b.apply(this, arguments);
    }, R);
  }, count: function(P) {
    var b = 0;
    return ie(P, function() {
      b++;
    }), b;
  }, toArray: function(P) {
    return ie(P, function(b) {
      return b;
    }) || [];
  }, only: function(P) {
    if (!G(P)) throw Error("React.Children.only expected to receive a single React element child.");
    return P;
  } }, Ie.Component = _, Ie.Fragment = i, Ie.Profiler = a, Ie.PureComponent = k, Ie.StrictMode = o, Ie.Suspense = d, Ie.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = ae, Ie.act = z, Ie.cloneElement = function(P, b, R) {
    if (P == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + P + ".");
    var C = v({}, P.props), I = P.key, B = P.ref, X = P._owner;
    if (b != null) {
      if (b.ref !== void 0 && (B = b.ref, X = x.current), b.key !== void 0 && (I = "" + b.key), P.type && P.type.defaultProps) var J = P.type.defaultProps;
      for (se in b) N.call(b, se) && !F.hasOwnProperty(se) && (C[se] = b[se] === void 0 && J !== void 0 ? J[se] : b[se]);
    }
    var se = arguments.length - 2;
    if (se === 1) C.children = R;
    else if (1 < se) {
      J = Array(se);
      for (var ce = 0; ce < se; ce++) J[ce] = arguments[ce + 2];
      C.children = J;
    }
    return { $$typeof: e, type: P.type, key: I, ref: B, props: C, _owner: X };
  }, Ie.createContext = function(P) {
    return P = { $$typeof: c, _currentValue: P, _currentValue2: P, _threadCount: 0, Provider: null, Consumer: null, _defaultValue: null, _globalName: null }, P.Provider = { $$typeof: l, _context: P }, P.Consumer = P;
  }, Ie.createElement = V, Ie.createFactory = function(P) {
    var b = V.bind(null, P);
    return b.type = P, b;
  }, Ie.createRef = function() {
    return { current: null };
  }, Ie.forwardRef = function(P) {
    return { $$typeof: f, render: P };
  }, Ie.isValidElement = G, Ie.lazy = function(P) {
    return { $$typeof: y, _payload: { _status: -1, _result: P }, _init: ne };
  }, Ie.memo = function(P, b) {
    return { $$typeof: m, type: P, compare: b === void 0 ? null : b };
  }, Ie.startTransition = function(P) {
    var b = Z.transition;
    Z.transition = {};
    try {
      P();
    } finally {
      Z.transition = b;
    }
  }, Ie.unstable_act = z, Ie.useCallback = function(P, b) {
    return pe.current.useCallback(P, b);
  }, Ie.useContext = function(P) {
    return pe.current.useContext(P);
  }, Ie.useDebugValue = function() {
  }, Ie.useDeferredValue = function(P) {
    return pe.current.useDeferredValue(P);
  }, Ie.useEffect = function(P, b) {
    return pe.current.useEffect(P, b);
  }, Ie.useId = function() {
    return pe.current.useId();
  }, Ie.useImperativeHandle = function(P, b, R) {
    return pe.current.useImperativeHandle(P, b, R);
  }, Ie.useInsertionEffect = function(P, b) {
    return pe.current.useInsertionEffect(P, b);
  }, Ie.useLayoutEffect = function(P, b) {
    return pe.current.useLayoutEffect(P, b);
  }, Ie.useMemo = function(P, b) {
    return pe.current.useMemo(P, b);
  }, Ie.useReducer = function(P, b, R) {
    return pe.current.useReducer(P, b, R);
  }, Ie.useRef = function(P) {
    return pe.current.useRef(P);
  }, Ie.useState = function(P) {
    return pe.current.useState(P);
  }, Ie.useSyncExternalStore = function(P, b, R) {
    return pe.current.useSyncExternalStore(P, b, R);
  }, Ie.useTransition = function() {
    return pe.current.useTransition();
  }, Ie.version = "18.3.1", Ie;
}
fv.exports = u1();
var fe = fv.exports;
const Gc = /* @__PURE__ */ zs(fe);
var dv = { exports: {} }, Vt = {}, Yc = { exports: {} }, Qc = {};
/**
 * @license React
 * scheduler.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var dy;
function c1() {
  return dy || (dy = 1, function(e) {
    function t(Z, ae) {
      var z = Z.length;
      Z.push(ae);
      e: for (; 0 < z; ) {
        var P = z - 1 >>> 1, b = Z[P];
        if (0 < a(b, ae)) Z[P] = ae, Z[z] = b, z = P;
        else break e;
      }
    }
    function i(Z) {
      return Z.length === 0 ? null : Z[0];
    }
    function o(Z) {
      if (Z.length === 0) return null;
      var ae = Z[0], z = Z.pop();
      if (z !== ae) {
        Z[0] = z;
        e: for (var P = 0, b = Z.length, R = b >>> 1; P < R; ) {
          var C = 2 * (P + 1) - 1, I = Z[C], B = C + 1, X = Z[B];
          if (0 > a(I, z)) B < b && 0 > a(X, I) ? (Z[P] = X, Z[B] = z, P = B) : (Z[P] = I, Z[C] = z, P = C);
          else if (B < b && 0 > a(X, z)) Z[P] = X, Z[B] = z, P = B;
          else break e;
        }
      }
      return ae;
    }
    function a(Z, ae) {
      var z = Z.sortIndex - ae.sortIndex;
      return z !== 0 ? z : Z.id - ae.id;
    }
    if (typeof performance == "object" && typeof performance.now == "function") {
      var l = performance;
      e.unstable_now = function() {
        return l.now();
      };
    } else {
      var c = Date, f = c.now();
      e.unstable_now = function() {
        return c.now() - f;
      };
    }
    var d = [], m = [], y = 1, h = null, S = 3, $ = !1, v = !1, w = !1, _ = typeof setTimeout == "function" ? setTimeout : null, E = typeof clearTimeout == "function" ? clearTimeout : null, k = typeof setImmediate < "u" ? setImmediate : null;
    typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
    function j(Z) {
      for (var ae = i(m); ae !== null; ) {
        if (ae.callback === null) o(m);
        else if (ae.startTime <= Z) o(m), ae.sortIndex = ae.expirationTime, t(d, ae);
        else break;
        ae = i(m);
      }
    }
    function T(Z) {
      if (w = !1, j(Z), !v) if (i(d) !== null) v = !0, ne(N);
      else {
        var ae = i(m);
        ae !== null && pe(T, ae.startTime - Z);
      }
    }
    function N(Z, ae) {
      v = !1, w && (w = !1, E(V), V = -1), $ = !0;
      var z = S;
      try {
        for (j(ae), h = i(d); h !== null && (!(h.expirationTime > ae) || Z && !Q()); ) {
          var P = h.callback;
          if (typeof P == "function") {
            h.callback = null, S = h.priorityLevel;
            var b = P(h.expirationTime <= ae);
            ae = e.unstable_now(), typeof b == "function" ? h.callback = b : h === i(d) && o(d), j(ae);
          } else o(d);
          h = i(d);
        }
        if (h !== null) var R = !0;
        else {
          var C = i(m);
          C !== null && pe(T, C.startTime - ae), R = !1;
        }
        return R;
      } finally {
        h = null, S = z, $ = !1;
      }
    }
    var x = !1, F = null, V = -1, U = 5, G = -1;
    function Q() {
      return !(e.unstable_now() - G < U);
    }
    function H() {
      if (F !== null) {
        var Z = e.unstable_now();
        G = Z;
        var ae = !0;
        try {
          ae = F(!0, Z);
        } finally {
          ae ? q() : (x = !1, F = null);
        }
      } else x = !1;
    }
    var q;
    if (typeof k == "function") q = function() {
      k(H);
    };
    else if (typeof MessageChannel < "u") {
      var le = new MessageChannel(), ie = le.port2;
      le.port1.onmessage = H, q = function() {
        ie.postMessage(null);
      };
    } else q = function() {
      _(H, 0);
    };
    function ne(Z) {
      F = Z, x || (x = !0, q());
    }
    function pe(Z, ae) {
      V = _(function() {
        Z(e.unstable_now());
      }, ae);
    }
    e.unstable_IdlePriority = 5, e.unstable_ImmediatePriority = 1, e.unstable_LowPriority = 4, e.unstable_NormalPriority = 3, e.unstable_Profiling = null, e.unstable_UserBlockingPriority = 2, e.unstable_cancelCallback = function(Z) {
      Z.callback = null;
    }, e.unstable_continueExecution = function() {
      v || $ || (v = !0, ne(N));
    }, e.unstable_forceFrameRate = function(Z) {
      0 > Z || 125 < Z ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : U = 0 < Z ? Math.floor(1e3 / Z) : 5;
    }, e.unstable_getCurrentPriorityLevel = function() {
      return S;
    }, e.unstable_getFirstCallbackNode = function() {
      return i(d);
    }, e.unstable_next = function(Z) {
      switch (S) {
        case 1:
        case 2:
        case 3:
          var ae = 3;
          break;
        default:
          ae = S;
      }
      var z = S;
      S = ae;
      try {
        return Z();
      } finally {
        S = z;
      }
    }, e.unstable_pauseExecution = function() {
    }, e.unstable_requestPaint = function() {
    }, e.unstable_runWithPriority = function(Z, ae) {
      switch (Z) {
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
          break;
        default:
          Z = 3;
      }
      var z = S;
      S = Z;
      try {
        return ae();
      } finally {
        S = z;
      }
    }, e.unstable_scheduleCallback = function(Z, ae, z) {
      var P = e.unstable_now();
      switch (typeof z == "object" && z !== null ? (z = z.delay, z = typeof z == "number" && 0 < z ? P + z : P) : z = P, Z) {
        case 1:
          var b = -1;
          break;
        case 2:
          b = 250;
          break;
        case 5:
          b = 1073741823;
          break;
        case 4:
          b = 1e4;
          break;
        default:
          b = 5e3;
      }
      return b = z + b, Z = { id: y++, callback: ae, priorityLevel: Z, startTime: z, expirationTime: b, sortIndex: -1 }, z > P ? (Z.sortIndex = z, t(m, Z), i(d) === null && Z === i(m) && (w ? (E(V), V = -1) : w = !0, pe(T, z - P))) : (Z.sortIndex = b, t(d, Z), v || $ || (v = !0, ne(N))), Z;
    }, e.unstable_shouldYield = Q, e.unstable_wrapCallback = function(Z) {
      var ae = S;
      return function() {
        var z = S;
        S = ae;
        try {
          return Z.apply(this, arguments);
        } finally {
          S = z;
        }
      };
    };
  }(Qc)), Qc;
}
var py;
function f1() {
  return py || (py = 1, Yc.exports = c1()), Yc.exports;
}
/**
 * @license React
 * react-dom.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var hy;
function d1() {
  if (hy) return Vt;
  hy = 1;
  var e = fe, t = f1();
  function i(n) {
    for (var r = "https://reactjs.org/docs/error-decoder.html?invariant=" + n, s = 1; s < arguments.length; s++) r += "&args[]=" + encodeURIComponent(arguments[s]);
    return "Minified React error #" + n + "; visit " + r + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
  }
  var o = /* @__PURE__ */ new Set(), a = {};
  function l(n, r) {
    c(n, r), c(n + "Capture", r);
  }
  function c(n, r) {
    for (a[n] = r, n = 0; n < r.length; n++) o.add(r[n]);
  }
  var f = !(typeof window > "u" || typeof window.document > "u" || typeof window.document.createElement > "u"), d = Object.prototype.hasOwnProperty, m = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, y = {}, h = {};
  function S(n) {
    return d.call(h, n) ? !0 : d.call(y, n) ? !1 : m.test(n) ? h[n] = !0 : (y[n] = !0, !1);
  }
  function $(n, r, s, u) {
    if (s !== null && s.type === 0) return !1;
    switch (typeof r) {
      case "function":
      case "symbol":
        return !0;
      case "boolean":
        return u ? !1 : s !== null ? !s.acceptsBooleans : (n = n.toLowerCase().slice(0, 5), n !== "data-" && n !== "aria-");
      default:
        return !1;
    }
  }
  function v(n, r, s, u) {
    if (r === null || typeof r > "u" || $(n, r, s, u)) return !0;
    if (u) return !1;
    if (s !== null) switch (s.type) {
      case 3:
        return !r;
      case 4:
        return r === !1;
      case 5:
        return isNaN(r);
      case 6:
        return isNaN(r) || 1 > r;
    }
    return !1;
  }
  function w(n, r, s, u, p, g, O) {
    this.acceptsBooleans = r === 2 || r === 3 || r === 4, this.attributeName = u, this.attributeNamespace = p, this.mustUseProperty = s, this.propertyName = n, this.type = r, this.sanitizeURL = g, this.removeEmptyString = O;
  }
  var _ = {};
  "children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(n) {
    _[n] = new w(n, 0, !1, n, null, !1, !1);
  }), [["acceptCharset", "accept-charset"], ["className", "class"], ["htmlFor", "for"], ["httpEquiv", "http-equiv"]].forEach(function(n) {
    var r = n[0];
    _[r] = new w(r, 1, !1, n[1], null, !1, !1);
  }), ["contentEditable", "draggable", "spellCheck", "value"].forEach(function(n) {
    _[n] = new w(n, 2, !1, n.toLowerCase(), null, !1, !1);
  }), ["autoReverse", "externalResourcesRequired", "focusable", "preserveAlpha"].forEach(function(n) {
    _[n] = new w(n, 2, !1, n, null, !1, !1);
  }), "allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(n) {
    _[n] = new w(n, 3, !1, n.toLowerCase(), null, !1, !1);
  }), ["checked", "multiple", "muted", "selected"].forEach(function(n) {
    _[n] = new w(n, 3, !0, n, null, !1, !1);
  }), ["capture", "download"].forEach(function(n) {
    _[n] = new w(n, 4, !1, n, null, !1, !1);
  }), ["cols", "rows", "size", "span"].forEach(function(n) {
    _[n] = new w(n, 6, !1, n, null, !1, !1);
  }), ["rowSpan", "start"].forEach(function(n) {
    _[n] = new w(n, 5, !1, n.toLowerCase(), null, !1, !1);
  });
  var E = /[\-:]([a-z])/g;
  function k(n) {
    return n[1].toUpperCase();
  }
  "accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(n) {
    var r = n.replace(
      E,
      k
    );
    _[r] = new w(r, 1, !1, n, null, !1, !1);
  }), "xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(n) {
    var r = n.replace(E, k);
    _[r] = new w(r, 1, !1, n, "http://www.w3.org/1999/xlink", !1, !1);
  }), ["xml:base", "xml:lang", "xml:space"].forEach(function(n) {
    var r = n.replace(E, k);
    _[r] = new w(r, 1, !1, n, "http://www.w3.org/XML/1998/namespace", !1, !1);
  }), ["tabIndex", "crossOrigin"].forEach(function(n) {
    _[n] = new w(n, 1, !1, n.toLowerCase(), null, !1, !1);
  }), _.xlinkHref = new w("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1), ["src", "href", "action", "formAction"].forEach(function(n) {
    _[n] = new w(n, 1, !1, n.toLowerCase(), null, !0, !0);
  });
  function j(n, r, s, u) {
    var p = _.hasOwnProperty(r) ? _[r] : null;
    (p !== null ? p.type !== 0 : u || !(2 < r.length) || r[0] !== "o" && r[0] !== "O" || r[1] !== "n" && r[1] !== "N") && (v(r, s, p, u) && (s = null), u || p === null ? S(r) && (s === null ? n.removeAttribute(r) : n.setAttribute(r, "" + s)) : p.mustUseProperty ? n[p.propertyName] = s === null ? p.type === 3 ? !1 : "" : s : (r = p.attributeName, u = p.attributeNamespace, s === null ? n.removeAttribute(r) : (p = p.type, s = p === 3 || p === 4 && s === !0 ? "" : "" + s, u ? n.setAttributeNS(u, r, s) : n.setAttribute(r, s))));
  }
  var T = e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, N = Symbol.for("react.element"), x = Symbol.for("react.portal"), F = Symbol.for("react.fragment"), V = Symbol.for("react.strict_mode"), U = Symbol.for("react.profiler"), G = Symbol.for("react.provider"), Q = Symbol.for("react.context"), H = Symbol.for("react.forward_ref"), q = Symbol.for("react.suspense"), le = Symbol.for("react.suspense_list"), ie = Symbol.for("react.memo"), ne = Symbol.for("react.lazy"), pe = Symbol.for("react.offscreen"), Z = Symbol.iterator;
  function ae(n) {
    return n === null || typeof n != "object" ? null : (n = Z && n[Z] || n["@@iterator"], typeof n == "function" ? n : null);
  }
  var z = Object.assign, P;
  function b(n) {
    if (P === void 0) try {
      throw Error();
    } catch (s) {
      var r = s.stack.trim().match(/\n( *(at )?)/);
      P = r && r[1] || "";
    }
    return `
` + P + n;
  }
  var R = !1;
  function C(n, r) {
    if (!n || R) return "";
    R = !0;
    var s = Error.prepareStackTrace;
    Error.prepareStackTrace = void 0;
    try {
      if (r) if (r = function() {
        throw Error();
      }, Object.defineProperty(r.prototype, "props", { set: function() {
        throw Error();
      } }), typeof Reflect == "object" && Reflect.construct) {
        try {
          Reflect.construct(r, []);
        } catch (Y) {
          var u = Y;
        }
        Reflect.construct(n, [], r);
      } else {
        try {
          r.call();
        } catch (Y) {
          u = Y;
        }
        n.call(r.prototype);
      }
      else {
        try {
          throw Error();
        } catch (Y) {
          u = Y;
        }
        n();
      }
    } catch (Y) {
      if (Y && u && typeof Y.stack == "string") {
        for (var p = Y.stack.split(`
`), g = u.stack.split(`
`), O = p.length - 1, A = g.length - 1; 1 <= O && 0 <= A && p[O] !== g[A]; ) A--;
        for (; 1 <= O && 0 <= A; O--, A--) if (p[O] !== g[A]) {
          if (O !== 1 || A !== 1)
            do
              if (O--, A--, 0 > A || p[O] !== g[A]) {
                var M = `
` + p[O].replace(" at new ", " at ");
                return n.displayName && M.includes("<anonymous>") && (M = M.replace("<anonymous>", n.displayName)), M;
              }
            while (1 <= O && 0 <= A);
          break;
        }
      }
    } finally {
      R = !1, Error.prepareStackTrace = s;
    }
    return (n = n ? n.displayName || n.name : "") ? b(n) : "";
  }
  function I(n) {
    switch (n.tag) {
      case 5:
        return b(n.type);
      case 16:
        return b("Lazy");
      case 13:
        return b("Suspense");
      case 19:
        return b("SuspenseList");
      case 0:
      case 2:
      case 15:
        return n = C(n.type, !1), n;
      case 11:
        return n = C(n.type.render, !1), n;
      case 1:
        return n = C(n.type, !0), n;
      default:
        return "";
    }
  }
  function B(n) {
    if (n == null) return null;
    if (typeof n == "function") return n.displayName || n.name || null;
    if (typeof n == "string") return n;
    switch (n) {
      case F:
        return "Fragment";
      case x:
        return "Portal";
      case U:
        return "Profiler";
      case V:
        return "StrictMode";
      case q:
        return "Suspense";
      case le:
        return "SuspenseList";
    }
    if (typeof n == "object") switch (n.$$typeof) {
      case Q:
        return (n.displayName || "Context") + ".Consumer";
      case G:
        return (n._context.displayName || "Context") + ".Provider";
      case H:
        var r = n.render;
        return n = n.displayName, n || (n = r.displayName || r.name || "", n = n !== "" ? "ForwardRef(" + n + ")" : "ForwardRef"), n;
      case ie:
        return r = n.displayName || null, r !== null ? r : B(n.type) || "Memo";
      case ne:
        r = n._payload, n = n._init;
        try {
          return B(n(r));
        } catch {
        }
    }
    return null;
  }
  function X(n) {
    var r = n.type;
    switch (n.tag) {
      case 24:
        return "Cache";
      case 9:
        return (r.displayName || "Context") + ".Consumer";
      case 10:
        return (r._context.displayName || "Context") + ".Provider";
      case 18:
        return "DehydratedFragment";
      case 11:
        return n = r.render, n = n.displayName || n.name || "", r.displayName || (n !== "" ? "ForwardRef(" + n + ")" : "ForwardRef");
      case 7:
        return "Fragment";
      case 5:
        return r;
      case 4:
        return "Portal";
      case 3:
        return "Root";
      case 6:
        return "Text";
      case 16:
        return B(r);
      case 8:
        return r === V ? "StrictMode" : "Mode";
      case 22:
        return "Offscreen";
      case 12:
        return "Profiler";
      case 21:
        return "Scope";
      case 13:
        return "Suspense";
      case 19:
        return "SuspenseList";
      case 25:
        return "TracingMarker";
      case 1:
      case 0:
      case 17:
      case 2:
      case 14:
      case 15:
        if (typeof r == "function") return r.displayName || r.name || null;
        if (typeof r == "string") return r;
    }
    return null;
  }
  function J(n) {
    switch (typeof n) {
      case "boolean":
      case "number":
      case "string":
      case "undefined":
        return n;
      case "object":
        return n;
      default:
        return "";
    }
  }
  function se(n) {
    var r = n.type;
    return (n = n.nodeName) && n.toLowerCase() === "input" && (r === "checkbox" || r === "radio");
  }
  function ce(n) {
    var r = se(n) ? "checked" : "value", s = Object.getOwnPropertyDescriptor(n.constructor.prototype, r), u = "" + n[r];
    if (!n.hasOwnProperty(r) && typeof s < "u" && typeof s.get == "function" && typeof s.set == "function") {
      var p = s.get, g = s.set;
      return Object.defineProperty(n, r, { configurable: !0, get: function() {
        return p.call(this);
      }, set: function(O) {
        u = "" + O, g.call(this, O);
      } }), Object.defineProperty(n, r, { enumerable: s.enumerable }), { getValue: function() {
        return u;
      }, setValue: function(O) {
        u = "" + O;
      }, stopTracking: function() {
        n._valueTracker = null, delete n[r];
      } };
    }
  }
  function $e(n) {
    n._valueTracker || (n._valueTracker = ce(n));
  }
  function nt(n) {
    if (!n) return !1;
    var r = n._valueTracker;
    if (!r) return !0;
    var s = r.getValue(), u = "";
    return n && (u = se(n) ? n.checked ? "true" : "false" : n.value), n = u, n !== s ? (r.setValue(n), !0) : !1;
  }
  function ot(n) {
    if (n = n || (typeof document < "u" ? document : void 0), typeof n > "u") return null;
    try {
      return n.activeElement || n.body;
    } catch {
      return n.body;
    }
  }
  function ze(n, r) {
    var s = r.checked;
    return z({}, r, { defaultChecked: void 0, defaultValue: void 0, value: void 0, checked: s ?? n._wrapperState.initialChecked });
  }
  function Rt(n, r) {
    var s = r.defaultValue == null ? "" : r.defaultValue, u = r.checked != null ? r.checked : r.defaultChecked;
    s = J(r.value != null ? r.value : s), n._wrapperState = { initialChecked: u, initialValue: s, controlled: r.type === "checkbox" || r.type === "radio" ? r.checked != null : r.value != null };
  }
  function et(n, r) {
    r = r.checked, r != null && j(n, "checked", r, !1);
  }
  function Wt(n, r) {
    et(n, r);
    var s = J(r.value), u = r.type;
    if (s != null) u === "number" ? (s === 0 && n.value === "" || n.value != s) && (n.value = "" + s) : n.value !== "" + s && (n.value = "" + s);
    else if (u === "submit" || u === "reset") {
      n.removeAttribute("value");
      return;
    }
    r.hasOwnProperty("value") ? Wn(n, r.type, s) : r.hasOwnProperty("defaultValue") && Wn(n, r.type, J(r.defaultValue)), r.checked == null && r.defaultChecked != null && (n.defaultChecked = !!r.defaultChecked);
  }
  function Pt(n, r, s) {
    if (r.hasOwnProperty("value") || r.hasOwnProperty("defaultValue")) {
      var u = r.type;
      if (!(u !== "submit" && u !== "reset" || r.value !== void 0 && r.value !== null)) return;
      r = "" + n._wrapperState.initialValue, s || r === n.value || (n.value = r), n.defaultValue = r;
    }
    s = n.name, s !== "" && (n.name = ""), n.defaultChecked = !!n._wrapperState.initialChecked, s !== "" && (n.name = s);
  }
  function Wn(n, r, s) {
    (r !== "number" || ot(n.ownerDocument) !== n) && (s == null ? n.defaultValue = "" + n._wrapperState.initialValue : n.defaultValue !== "" + s && (n.defaultValue = "" + s));
  }
  var $n = Array.isArray;
  function On(n, r, s, u) {
    if (n = n.options, r) {
      r = {};
      for (var p = 0; p < s.length; p++) r["$" + s[p]] = !0;
      for (s = 0; s < n.length; s++) p = r.hasOwnProperty("$" + n[s].value), n[s].selected !== p && (n[s].selected = p), p && u && (n[s].defaultSelected = !0);
    } else {
      for (s = "" + J(s), r = null, p = 0; p < n.length; p++) {
        if (n[p].value === s) {
          n[p].selected = !0, u && (n[p].defaultSelected = !0);
          return;
        }
        r !== null || n[p].disabled || (r = n[p]);
      }
      r !== null && (r.selected = !0);
    }
  }
  function Br(n, r) {
    if (r.dangerouslySetInnerHTML != null) throw Error(i(91));
    return z({}, r, { value: void 0, defaultValue: void 0, children: "" + n._wrapperState.initialValue });
  }
  function ki(n, r) {
    var s = r.value;
    if (s == null) {
      if (s = r.children, r = r.defaultValue, s != null) {
        if (r != null) throw Error(i(92));
        if ($n(s)) {
          if (1 < s.length) throw Error(i(93));
          s = s[0];
        }
        r = s;
      }
      r == null && (r = ""), s = r;
    }
    n._wrapperState = { initialValue: J(s) };
  }
  function Ti(n, r) {
    var s = J(r.value), u = J(r.defaultValue);
    s != null && (s = "" + s, s !== n.value && (n.value = s), r.defaultValue == null && n.defaultValue !== s && (n.defaultValue = s)), u != null && (n.defaultValue = "" + u);
  }
  function Ni(n) {
    var r = n.textContent;
    r === n._wrapperState.initialValue && r !== "" && r !== null && (n.value = r);
  }
  function lr(n) {
    switch (n) {
      case "svg":
        return "http://www.w3.org/2000/svg";
      case "math":
        return "http://www.w3.org/1998/Math/MathML";
      default:
        return "http://www.w3.org/1999/xhtml";
    }
  }
  function Kr(n, r) {
    return n == null || n === "http://www.w3.org/1999/xhtml" ? lr(r) : n === "http://www.w3.org/2000/svg" && r === "foreignObject" ? "http://www.w3.org/1999/xhtml" : n;
  }
  var Wr, ko = function(n) {
    return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(r, s, u, p) {
      MSApp.execUnsafeLocalFunction(function() {
        return n(r, s, u, p);
      });
    } : n;
  }(function(n, r) {
    if (n.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in n) n.innerHTML = r;
    else {
      for (Wr = Wr || document.createElement("div"), Wr.innerHTML = "<svg>" + r.valueOf().toString() + "</svg>", r = Wr.firstChild; n.firstChild; ) n.removeChild(n.firstChild);
      for (; r.firstChild; ) n.appendChild(r.firstChild);
    }
  });
  function Hr(n, r) {
    if (r) {
      var s = n.firstChild;
      if (s && s === n.lastChild && s.nodeType === 3) {
        s.nodeValue = r;
        return;
      }
    }
    n.textContent = r;
  }
  var To = {
    animationIterationCount: !0,
    aspectRatio: !0,
    borderImageOutset: !0,
    borderImageSlice: !0,
    borderImageWidth: !0,
    boxFlex: !0,
    boxFlexGroup: !0,
    boxOrdinalGroup: !0,
    columnCount: !0,
    columns: !0,
    flex: !0,
    flexGrow: !0,
    flexPositive: !0,
    flexShrink: !0,
    flexNegative: !0,
    flexOrder: !0,
    gridArea: !0,
    gridRow: !0,
    gridRowEnd: !0,
    gridRowSpan: !0,
    gridRowStart: !0,
    gridColumn: !0,
    gridColumnEnd: !0,
    gridColumnSpan: !0,
    gridColumnStart: !0,
    fontWeight: !0,
    lineClamp: !0,
    lineHeight: !0,
    opacity: !0,
    order: !0,
    orphans: !0,
    tabSize: !0,
    widows: !0,
    zIndex: !0,
    zoom: !0,
    fillOpacity: !0,
    floodOpacity: !0,
    stopOpacity: !0,
    strokeDasharray: !0,
    strokeDashoffset: !0,
    strokeMiterlimit: !0,
    strokeOpacity: !0,
    strokeWidth: !0
  }, fS = ["Webkit", "ms", "Moz", "O"];
  Object.keys(To).forEach(function(n) {
    fS.forEach(function(r) {
      r = r + n.charAt(0).toUpperCase() + n.substring(1), To[r] = To[n];
    });
  });
  function Cp(n, r, s) {
    return r == null || typeof r == "boolean" || r === "" ? "" : s || typeof r != "number" || r === 0 || To.hasOwnProperty(n) && To[n] ? ("" + r).trim() : r + "px";
  }
  function kp(n, r) {
    n = n.style;
    for (var s in r) if (r.hasOwnProperty(s)) {
      var u = s.indexOf("--") === 0, p = Cp(s, r[s], u);
      s === "float" && (s = "cssFloat"), u ? n.setProperty(s, p) : n[s] = p;
    }
  }
  var dS = z({ menuitem: !0 }, { area: !0, base: !0, br: !0, col: !0, embed: !0, hr: !0, img: !0, input: !0, keygen: !0, link: !0, meta: !0, param: !0, source: !0, track: !0, wbr: !0 });
  function su(n, r) {
    if (r) {
      if (dS[n] && (r.children != null || r.dangerouslySetInnerHTML != null)) throw Error(i(137, n));
      if (r.dangerouslySetInnerHTML != null) {
        if (r.children != null) throw Error(i(60));
        if (typeof r.dangerouslySetInnerHTML != "object" || !("__html" in r.dangerouslySetInnerHTML)) throw Error(i(61));
      }
      if (r.style != null && typeof r.style != "object") throw Error(i(62));
    }
  }
  function au(n, r) {
    if (n.indexOf("-") === -1) return typeof r.is == "string";
    switch (n) {
      case "annotation-xml":
      case "color-profile":
      case "font-face":
      case "font-face-src":
      case "font-face-uri":
      case "font-face-format":
      case "font-face-name":
      case "missing-glyph":
        return !1;
      default:
        return !0;
    }
  }
  var lu = null;
  function uu(n) {
    return n = n.target || n.srcElement || window, n.correspondingUseElement && (n = n.correspondingUseElement), n.nodeType === 3 ? n.parentNode : n;
  }
  var cu = null, Ii = null, ji = null;
  function Tp(n) {
    if (n = Qo(n)) {
      if (typeof cu != "function") throw Error(i(280));
      var r = n.stateNode;
      r && (r = Ea(r), cu(n.stateNode, n.type, r));
    }
  }
  function Np(n) {
    Ii ? ji ? ji.push(n) : ji = [n] : Ii = n;
  }
  function Ip() {
    if (Ii) {
      var n = Ii, r = ji;
      if (ji = Ii = null, Tp(n), r) for (n = 0; n < r.length; n++) Tp(r[n]);
    }
  }
  function jp(n, r) {
    return n(r);
  }
  function Ap() {
  }
  var fu = !1;
  function xp(n, r, s) {
    if (fu) return n(r, s);
    fu = !0;
    try {
      return jp(n, r, s);
    } finally {
      fu = !1, (Ii !== null || ji !== null) && (Ap(), Ip());
    }
  }
  function No(n, r) {
    var s = n.stateNode;
    if (s === null) return null;
    var u = Ea(s);
    if (u === null) return null;
    s = u[r];
    e: switch (r) {
      case "onClick":
      case "onClickCapture":
      case "onDoubleClick":
      case "onDoubleClickCapture":
      case "onMouseDown":
      case "onMouseDownCapture":
      case "onMouseMove":
      case "onMouseMoveCapture":
      case "onMouseUp":
      case "onMouseUpCapture":
      case "onMouseEnter":
        (u = !u.disabled) || (n = n.type, u = !(n === "button" || n === "input" || n === "select" || n === "textarea")), n = !u;
        break e;
      default:
        n = !1;
    }
    if (n) return null;
    if (s && typeof s != "function") throw Error(i(231, r, typeof s));
    return s;
  }
  var du = !1;
  if (f) try {
    var Io = {};
    Object.defineProperty(Io, "passive", { get: function() {
      du = !0;
    } }), window.addEventListener("test", Io, Io), window.removeEventListener("test", Io, Io);
  } catch {
    du = !1;
  }
  function pS(n, r, s, u, p, g, O, A, M) {
    var Y = Array.prototype.slice.call(arguments, 3);
    try {
      r.apply(s, Y);
    } catch (te) {
      this.onError(te);
    }
  }
  var jo = !1, ea = null, ta = !1, pu = null, hS = { onError: function(n) {
    jo = !0, ea = n;
  } };
  function mS(n, r, s, u, p, g, O, A, M) {
    jo = !1, ea = null, pS.apply(hS, arguments);
  }
  function yS(n, r, s, u, p, g, O, A, M) {
    if (mS.apply(this, arguments), jo) {
      if (jo) {
        var Y = ea;
        jo = !1, ea = null;
      } else throw Error(i(198));
      ta || (ta = !0, pu = Y);
    }
  }
  function qr(n) {
    var r = n, s = n;
    if (n.alternate) for (; r.return; ) r = r.return;
    else {
      n = r;
      do
        r = n, r.flags & 4098 && (s = r.return), n = r.return;
      while (n);
    }
    return r.tag === 3 ? s : null;
  }
  function bp(n) {
    if (n.tag === 13) {
      var r = n.memoizedState;
      if (r === null && (n = n.alternate, n !== null && (r = n.memoizedState)), r !== null) return r.dehydrated;
    }
    return null;
  }
  function Fp(n) {
    if (qr(n) !== n) throw Error(i(188));
  }
  function gS(n) {
    var r = n.alternate;
    if (!r) {
      if (r = qr(n), r === null) throw Error(i(188));
      return r !== n ? null : n;
    }
    for (var s = n, u = r; ; ) {
      var p = s.return;
      if (p === null) break;
      var g = p.alternate;
      if (g === null) {
        if (u = p.return, u !== null) {
          s = u;
          continue;
        }
        break;
      }
      if (p.child === g.child) {
        for (g = p.child; g; ) {
          if (g === s) return Fp(p), n;
          if (g === u) return Fp(p), r;
          g = g.sibling;
        }
        throw Error(i(188));
      }
      if (s.return !== u.return) s = p, u = g;
      else {
        for (var O = !1, A = p.child; A; ) {
          if (A === s) {
            O = !0, s = p, u = g;
            break;
          }
          if (A === u) {
            O = !0, u = p, s = g;
            break;
          }
          A = A.sibling;
        }
        if (!O) {
          for (A = g.child; A; ) {
            if (A === s) {
              O = !0, s = g, u = p;
              break;
            }
            if (A === u) {
              O = !0, u = g, s = p;
              break;
            }
            A = A.sibling;
          }
          if (!O) throw Error(i(189));
        }
      }
      if (s.alternate !== u) throw Error(i(190));
    }
    if (s.tag !== 3) throw Error(i(188));
    return s.stateNode.current === s ? n : r;
  }
  function Rp(n) {
    return n = gS(n), n !== null ? Dp(n) : null;
  }
  function Dp(n) {
    if (n.tag === 5 || n.tag === 6) return n;
    for (n = n.child; n !== null; ) {
      var r = Dp(n);
      if (r !== null) return r;
      n = n.sibling;
    }
    return null;
  }
  var Mp = t.unstable_scheduleCallback, Lp = t.unstable_cancelCallback, vS = t.unstable_shouldYield, _S = t.unstable_requestPaint, at = t.unstable_now, SS = t.unstable_getCurrentPriorityLevel, hu = t.unstable_ImmediatePriority, Up = t.unstable_UserBlockingPriority, na = t.unstable_NormalPriority, wS = t.unstable_LowPriority, zp = t.unstable_IdlePriority, ra = null, Pn = null;
  function ES(n) {
    if (Pn && typeof Pn.onCommitFiberRoot == "function") try {
      Pn.onCommitFiberRoot(ra, n, void 0, (n.current.flags & 128) === 128);
    } catch {
    }
  }
  var un = Math.clz32 ? Math.clz32 : PS, $S = Math.log, OS = Math.LN2;
  function PS(n) {
    return n >>>= 0, n === 0 ? 32 : 31 - ($S(n) / OS | 0) | 0;
  }
  var ia = 64, oa = 4194304;
  function Ao(n) {
    switch (n & -n) {
      case 1:
        return 1;
      case 2:
        return 2;
      case 4:
        return 4;
      case 8:
        return 8;
      case 16:
        return 16;
      case 32:
        return 32;
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return n & 4194240;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return n & 130023424;
      case 134217728:
        return 134217728;
      case 268435456:
        return 268435456;
      case 536870912:
        return 536870912;
      case 1073741824:
        return 1073741824;
      default:
        return n;
    }
  }
  function sa(n, r) {
    var s = n.pendingLanes;
    if (s === 0) return 0;
    var u = 0, p = n.suspendedLanes, g = n.pingedLanes, O = s & 268435455;
    if (O !== 0) {
      var A = O & ~p;
      A !== 0 ? u = Ao(A) : (g &= O, g !== 0 && (u = Ao(g)));
    } else O = s & ~p, O !== 0 ? u = Ao(O) : g !== 0 && (u = Ao(g));
    if (u === 0) return 0;
    if (r !== 0 && r !== u && !(r & p) && (p = u & -u, g = r & -r, p >= g || p === 16 && (g & 4194240) !== 0)) return r;
    if (u & 4 && (u |= s & 16), r = n.entangledLanes, r !== 0) for (n = n.entanglements, r &= u; 0 < r; ) s = 31 - un(r), p = 1 << s, u |= n[s], r &= ~p;
    return u;
  }
  function CS(n, r) {
    switch (n) {
      case 1:
      case 2:
      case 4:
        return r + 250;
      case 8:
      case 16:
      case 32:
      case 64:
      case 128:
      case 256:
      case 512:
      case 1024:
      case 2048:
      case 4096:
      case 8192:
      case 16384:
      case 32768:
      case 65536:
      case 131072:
      case 262144:
      case 524288:
      case 1048576:
      case 2097152:
        return r + 5e3;
      case 4194304:
      case 8388608:
      case 16777216:
      case 33554432:
      case 67108864:
        return -1;
      case 134217728:
      case 268435456:
      case 536870912:
      case 1073741824:
        return -1;
      default:
        return -1;
    }
  }
  function kS(n, r) {
    for (var s = n.suspendedLanes, u = n.pingedLanes, p = n.expirationTimes, g = n.pendingLanes; 0 < g; ) {
      var O = 31 - un(g), A = 1 << O, M = p[O];
      M === -1 ? (!(A & s) || A & u) && (p[O] = CS(A, r)) : M <= r && (n.expiredLanes |= A), g &= ~A;
    }
  }
  function mu(n) {
    return n = n.pendingLanes & -1073741825, n !== 0 ? n : n & 1073741824 ? 1073741824 : 0;
  }
  function Vp() {
    var n = ia;
    return ia <<= 1, !(ia & 4194240) && (ia = 64), n;
  }
  function yu(n) {
    for (var r = [], s = 0; 31 > s; s++) r.push(n);
    return r;
  }
  function xo(n, r, s) {
    n.pendingLanes |= r, r !== 536870912 && (n.suspendedLanes = 0, n.pingedLanes = 0), n = n.eventTimes, r = 31 - un(r), n[r] = s;
  }
  function TS(n, r) {
    var s = n.pendingLanes & ~r;
    n.pendingLanes = r, n.suspendedLanes = 0, n.pingedLanes = 0, n.expiredLanes &= r, n.mutableReadLanes &= r, n.entangledLanes &= r, r = n.entanglements;
    var u = n.eventTimes;
    for (n = n.expirationTimes; 0 < s; ) {
      var p = 31 - un(s), g = 1 << p;
      r[p] = 0, u[p] = -1, n[p] = -1, s &= ~g;
    }
  }
  function gu(n, r) {
    var s = n.entangledLanes |= r;
    for (n = n.entanglements; s; ) {
      var u = 31 - un(s), p = 1 << u;
      p & r | n[u] & r && (n[u] |= r), s &= ~p;
    }
  }
  var Ve = 0;
  function Bp(n) {
    return n &= -n, 1 < n ? 4 < n ? n & 268435455 ? 16 : 536870912 : 4 : 1;
  }
  var Kp, vu, Wp, Hp, qp, _u = !1, aa = [], ur = null, cr = null, fr = null, bo = /* @__PURE__ */ new Map(), Fo = /* @__PURE__ */ new Map(), dr = [], NS = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
  function Gp(n, r) {
    switch (n) {
      case "focusin":
      case "focusout":
        ur = null;
        break;
      case "dragenter":
      case "dragleave":
        cr = null;
        break;
      case "mouseover":
      case "mouseout":
        fr = null;
        break;
      case "pointerover":
      case "pointerout":
        bo.delete(r.pointerId);
        break;
      case "gotpointercapture":
      case "lostpointercapture":
        Fo.delete(r.pointerId);
    }
  }
  function Ro(n, r, s, u, p, g) {
    return n === null || n.nativeEvent !== g ? (n = { blockedOn: r, domEventName: s, eventSystemFlags: u, nativeEvent: g, targetContainers: [p] }, r !== null && (r = Qo(r), r !== null && vu(r)), n) : (n.eventSystemFlags |= u, r = n.targetContainers, p !== null && r.indexOf(p) === -1 && r.push(p), n);
  }
  function IS(n, r, s, u, p) {
    switch (r) {
      case "focusin":
        return ur = Ro(ur, n, r, s, u, p), !0;
      case "dragenter":
        return cr = Ro(cr, n, r, s, u, p), !0;
      case "mouseover":
        return fr = Ro(fr, n, r, s, u, p), !0;
      case "pointerover":
        var g = p.pointerId;
        return bo.set(g, Ro(bo.get(g) || null, n, r, s, u, p)), !0;
      case "gotpointercapture":
        return g = p.pointerId, Fo.set(g, Ro(Fo.get(g) || null, n, r, s, u, p)), !0;
    }
    return !1;
  }
  function Yp(n) {
    var r = Gr(n.target);
    if (r !== null) {
      var s = qr(r);
      if (s !== null) {
        if (r = s.tag, r === 13) {
          if (r = bp(s), r !== null) {
            n.blockedOn = r, qp(n.priority, function() {
              Wp(s);
            });
            return;
          }
        } else if (r === 3 && s.stateNode.current.memoizedState.isDehydrated) {
          n.blockedOn = s.tag === 3 ? s.stateNode.containerInfo : null;
          return;
        }
      }
    }
    n.blockedOn = null;
  }
  function la(n) {
    if (n.blockedOn !== null) return !1;
    for (var r = n.targetContainers; 0 < r.length; ) {
      var s = wu(n.domEventName, n.eventSystemFlags, r[0], n.nativeEvent);
      if (s === null) {
        s = n.nativeEvent;
        var u = new s.constructor(s.type, s);
        lu = u, s.target.dispatchEvent(u), lu = null;
      } else return r = Qo(s), r !== null && vu(r), n.blockedOn = s, !1;
      r.shift();
    }
    return !0;
  }
  function Qp(n, r, s) {
    la(n) && s.delete(r);
  }
  function jS() {
    _u = !1, ur !== null && la(ur) && (ur = null), cr !== null && la(cr) && (cr = null), fr !== null && la(fr) && (fr = null), bo.forEach(Qp), Fo.forEach(Qp);
  }
  function Do(n, r) {
    n.blockedOn === r && (n.blockedOn = null, _u || (_u = !0, t.unstable_scheduleCallback(t.unstable_NormalPriority, jS)));
  }
  function Mo(n) {
    function r(p) {
      return Do(p, n);
    }
    if (0 < aa.length) {
      Do(aa[0], n);
      for (var s = 1; s < aa.length; s++) {
        var u = aa[s];
        u.blockedOn === n && (u.blockedOn = null);
      }
    }
    for (ur !== null && Do(ur, n), cr !== null && Do(cr, n), fr !== null && Do(fr, n), bo.forEach(r), Fo.forEach(r), s = 0; s < dr.length; s++) u = dr[s], u.blockedOn === n && (u.blockedOn = null);
    for (; 0 < dr.length && (s = dr[0], s.blockedOn === null); ) Yp(s), s.blockedOn === null && dr.shift();
  }
  var Ai = T.ReactCurrentBatchConfig, ua = !0;
  function AS(n, r, s, u) {
    var p = Ve, g = Ai.transition;
    Ai.transition = null;
    try {
      Ve = 1, Su(n, r, s, u);
    } finally {
      Ve = p, Ai.transition = g;
    }
  }
  function xS(n, r, s, u) {
    var p = Ve, g = Ai.transition;
    Ai.transition = null;
    try {
      Ve = 4, Su(n, r, s, u);
    } finally {
      Ve = p, Ai.transition = g;
    }
  }
  function Su(n, r, s, u) {
    if (ua) {
      var p = wu(n, r, s, u);
      if (p === null) Mu(n, r, u, ca, s), Gp(n, u);
      else if (IS(p, n, r, s, u)) u.stopPropagation();
      else if (Gp(n, u), r & 4 && -1 < NS.indexOf(n)) {
        for (; p !== null; ) {
          var g = Qo(p);
          if (g !== null && Kp(g), g = wu(n, r, s, u), g === null && Mu(n, r, u, ca, s), g === p) break;
          p = g;
        }
        p !== null && u.stopPropagation();
      } else Mu(n, r, u, null, s);
    }
  }
  var ca = null;
  function wu(n, r, s, u) {
    if (ca = null, n = uu(u), n = Gr(n), n !== null) if (r = qr(n), r === null) n = null;
    else if (s = r.tag, s === 13) {
      if (n = bp(r), n !== null) return n;
      n = null;
    } else if (s === 3) {
      if (r.stateNode.current.memoizedState.isDehydrated) return r.tag === 3 ? r.stateNode.containerInfo : null;
      n = null;
    } else r !== n && (n = null);
    return ca = n, null;
  }
  function Jp(n) {
    switch (n) {
      case "cancel":
      case "click":
      case "close":
      case "contextmenu":
      case "copy":
      case "cut":
      case "auxclick":
      case "dblclick":
      case "dragend":
      case "dragstart":
      case "drop":
      case "focusin":
      case "focusout":
      case "input":
      case "invalid":
      case "keydown":
      case "keypress":
      case "keyup":
      case "mousedown":
      case "mouseup":
      case "paste":
      case "pause":
      case "play":
      case "pointercancel":
      case "pointerdown":
      case "pointerup":
      case "ratechange":
      case "reset":
      case "resize":
      case "seeked":
      case "submit":
      case "touchcancel":
      case "touchend":
      case "touchstart":
      case "volumechange":
      case "change":
      case "selectionchange":
      case "textInput":
      case "compositionstart":
      case "compositionend":
      case "compositionupdate":
      case "beforeblur":
      case "afterblur":
      case "beforeinput":
      case "blur":
      case "fullscreenchange":
      case "focus":
      case "hashchange":
      case "popstate":
      case "select":
      case "selectstart":
        return 1;
      case "drag":
      case "dragenter":
      case "dragexit":
      case "dragleave":
      case "dragover":
      case "mousemove":
      case "mouseout":
      case "mouseover":
      case "pointermove":
      case "pointerout":
      case "pointerover":
      case "scroll":
      case "toggle":
      case "touchmove":
      case "wheel":
      case "mouseenter":
      case "mouseleave":
      case "pointerenter":
      case "pointerleave":
        return 4;
      case "message":
        switch (SS()) {
          case hu:
            return 1;
          case Up:
            return 4;
          case na:
          case wS:
            return 16;
          case zp:
            return 536870912;
          default:
            return 16;
        }
      default:
        return 16;
    }
  }
  var pr = null, Eu = null, fa = null;
  function Xp() {
    if (fa) return fa;
    var n, r = Eu, s = r.length, u, p = "value" in pr ? pr.value : pr.textContent, g = p.length;
    for (n = 0; n < s && r[n] === p[n]; n++) ;
    var O = s - n;
    for (u = 1; u <= O && r[s - u] === p[g - u]; u++) ;
    return fa = p.slice(n, 1 < u ? 1 - u : void 0);
  }
  function da(n) {
    var r = n.keyCode;
    return "charCode" in n ? (n = n.charCode, n === 0 && r === 13 && (n = 13)) : n = r, n === 10 && (n = 13), 32 <= n || n === 13 ? n : 0;
  }
  function pa() {
    return !0;
  }
  function Zp() {
    return !1;
  }
  function Ht(n) {
    function r(s, u, p, g, O) {
      this._reactName = s, this._targetInst = p, this.type = u, this.nativeEvent = g, this.target = O, this.currentTarget = null;
      for (var A in n) n.hasOwnProperty(A) && (s = n[A], this[A] = s ? s(g) : g[A]);
      return this.isDefaultPrevented = (g.defaultPrevented != null ? g.defaultPrevented : g.returnValue === !1) ? pa : Zp, this.isPropagationStopped = Zp, this;
    }
    return z(r.prototype, { preventDefault: function() {
      this.defaultPrevented = !0;
      var s = this.nativeEvent;
      s && (s.preventDefault ? s.preventDefault() : typeof s.returnValue != "unknown" && (s.returnValue = !1), this.isDefaultPrevented = pa);
    }, stopPropagation: function() {
      var s = this.nativeEvent;
      s && (s.stopPropagation ? s.stopPropagation() : typeof s.cancelBubble != "unknown" && (s.cancelBubble = !0), this.isPropagationStopped = pa);
    }, persist: function() {
    }, isPersistent: pa }), r;
  }
  var xi = { eventPhase: 0, bubbles: 0, cancelable: 0, timeStamp: function(n) {
    return n.timeStamp || Date.now();
  }, defaultPrevented: 0, isTrusted: 0 }, $u = Ht(xi), Lo = z({}, xi, { view: 0, detail: 0 }), bS = Ht(Lo), Ou, Pu, Uo, ha = z({}, Lo, { screenX: 0, screenY: 0, clientX: 0, clientY: 0, pageX: 0, pageY: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, getModifierState: ku, button: 0, buttons: 0, relatedTarget: function(n) {
    return n.relatedTarget === void 0 ? n.fromElement === n.srcElement ? n.toElement : n.fromElement : n.relatedTarget;
  }, movementX: function(n) {
    return "movementX" in n ? n.movementX : (n !== Uo && (Uo && n.type === "mousemove" ? (Ou = n.screenX - Uo.screenX, Pu = n.screenY - Uo.screenY) : Pu = Ou = 0, Uo = n), Ou);
  }, movementY: function(n) {
    return "movementY" in n ? n.movementY : Pu;
  } }), eh = Ht(ha), FS = z({}, ha, { dataTransfer: 0 }), RS = Ht(FS), DS = z({}, Lo, { relatedTarget: 0 }), Cu = Ht(DS), MS = z({}, xi, { animationName: 0, elapsedTime: 0, pseudoElement: 0 }), LS = Ht(MS), US = z({}, xi, { clipboardData: function(n) {
    return "clipboardData" in n ? n.clipboardData : window.clipboardData;
  } }), zS = Ht(US), VS = z({}, xi, { data: 0 }), th = Ht(VS), BS = {
    Esc: "Escape",
    Spacebar: " ",
    Left: "ArrowLeft",
    Up: "ArrowUp",
    Right: "ArrowRight",
    Down: "ArrowDown",
    Del: "Delete",
    Win: "OS",
    Menu: "ContextMenu",
    Apps: "ContextMenu",
    Scroll: "ScrollLock",
    MozPrintableKey: "Unidentified"
  }, KS = {
    8: "Backspace",
    9: "Tab",
    12: "Clear",
    13: "Enter",
    16: "Shift",
    17: "Control",
    18: "Alt",
    19: "Pause",
    20: "CapsLock",
    27: "Escape",
    32: " ",
    33: "PageUp",
    34: "PageDown",
    35: "End",
    36: "Home",
    37: "ArrowLeft",
    38: "ArrowUp",
    39: "ArrowRight",
    40: "ArrowDown",
    45: "Insert",
    46: "Delete",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
    144: "NumLock",
    145: "ScrollLock",
    224: "Meta"
  }, WS = { Alt: "altKey", Control: "ctrlKey", Meta: "metaKey", Shift: "shiftKey" };
  function HS(n) {
    var r = this.nativeEvent;
    return r.getModifierState ? r.getModifierState(n) : (n = WS[n]) ? !!r[n] : !1;
  }
  function ku() {
    return HS;
  }
  var qS = z({}, Lo, { key: function(n) {
    if (n.key) {
      var r = BS[n.key] || n.key;
      if (r !== "Unidentified") return r;
    }
    return n.type === "keypress" ? (n = da(n), n === 13 ? "Enter" : String.fromCharCode(n)) : n.type === "keydown" || n.type === "keyup" ? KS[n.keyCode] || "Unidentified" : "";
  }, code: 0, location: 0, ctrlKey: 0, shiftKey: 0, altKey: 0, metaKey: 0, repeat: 0, locale: 0, getModifierState: ku, charCode: function(n) {
    return n.type === "keypress" ? da(n) : 0;
  }, keyCode: function(n) {
    return n.type === "keydown" || n.type === "keyup" ? n.keyCode : 0;
  }, which: function(n) {
    return n.type === "keypress" ? da(n) : n.type === "keydown" || n.type === "keyup" ? n.keyCode : 0;
  } }), GS = Ht(qS), YS = z({}, ha, { pointerId: 0, width: 0, height: 0, pressure: 0, tangentialPressure: 0, tiltX: 0, tiltY: 0, twist: 0, pointerType: 0, isPrimary: 0 }), nh = Ht(YS), QS = z({}, Lo, { touches: 0, targetTouches: 0, changedTouches: 0, altKey: 0, metaKey: 0, ctrlKey: 0, shiftKey: 0, getModifierState: ku }), JS = Ht(QS), XS = z({}, xi, { propertyName: 0, elapsedTime: 0, pseudoElement: 0 }), ZS = Ht(XS), ew = z({}, ha, {
    deltaX: function(n) {
      return "deltaX" in n ? n.deltaX : "wheelDeltaX" in n ? -n.wheelDeltaX : 0;
    },
    deltaY: function(n) {
      return "deltaY" in n ? n.deltaY : "wheelDeltaY" in n ? -n.wheelDeltaY : "wheelDelta" in n ? -n.wheelDelta : 0;
    },
    deltaZ: 0,
    deltaMode: 0
  }), tw = Ht(ew), nw = [9, 13, 27, 32], Tu = f && "CompositionEvent" in window, zo = null;
  f && "documentMode" in document && (zo = document.documentMode);
  var rw = f && "TextEvent" in window && !zo, rh = f && (!Tu || zo && 8 < zo && 11 >= zo), ih = " ", oh = !1;
  function sh(n, r) {
    switch (n) {
      case "keyup":
        return nw.indexOf(r.keyCode) !== -1;
      case "keydown":
        return r.keyCode !== 229;
      case "keypress":
      case "mousedown":
      case "focusout":
        return !0;
      default:
        return !1;
    }
  }
  function ah(n) {
    return n = n.detail, typeof n == "object" && "data" in n ? n.data : null;
  }
  var bi = !1;
  function iw(n, r) {
    switch (n) {
      case "compositionend":
        return ah(r);
      case "keypress":
        return r.which !== 32 ? null : (oh = !0, ih);
      case "textInput":
        return n = r.data, n === ih && oh ? null : n;
      default:
        return null;
    }
  }
  function ow(n, r) {
    if (bi) return n === "compositionend" || !Tu && sh(n, r) ? (n = Xp(), fa = Eu = pr = null, bi = !1, n) : null;
    switch (n) {
      case "paste":
        return null;
      case "keypress":
        if (!(r.ctrlKey || r.altKey || r.metaKey) || r.ctrlKey && r.altKey) {
          if (r.char && 1 < r.char.length) return r.char;
          if (r.which) return String.fromCharCode(r.which);
        }
        return null;
      case "compositionend":
        return rh && r.locale !== "ko" ? null : r.data;
      default:
        return null;
    }
  }
  var sw = { color: !0, date: !0, datetime: !0, "datetime-local": !0, email: !0, month: !0, number: !0, password: !0, range: !0, search: !0, tel: !0, text: !0, time: !0, url: !0, week: !0 };
  function lh(n) {
    var r = n && n.nodeName && n.nodeName.toLowerCase();
    return r === "input" ? !!sw[n.type] : r === "textarea";
  }
  function uh(n, r, s, u) {
    Np(u), r = _a(r, "onChange"), 0 < r.length && (s = new $u("onChange", "change", null, s, u), n.push({ event: s, listeners: r }));
  }
  var Vo = null, Bo = null;
  function aw(n) {
    kh(n, 0);
  }
  function ma(n) {
    var r = Li(n);
    if (nt(r)) return n;
  }
  function lw(n, r) {
    if (n === "change") return r;
  }
  var ch = !1;
  if (f) {
    var Nu;
    if (f) {
      var Iu = "oninput" in document;
      if (!Iu) {
        var fh = document.createElement("div");
        fh.setAttribute("oninput", "return;"), Iu = typeof fh.oninput == "function";
      }
      Nu = Iu;
    } else Nu = !1;
    ch = Nu && (!document.documentMode || 9 < document.documentMode);
  }
  function dh() {
    Vo && (Vo.detachEvent("onpropertychange", ph), Bo = Vo = null);
  }
  function ph(n) {
    if (n.propertyName === "value" && ma(Bo)) {
      var r = [];
      uh(r, Bo, n, uu(n)), xp(aw, r);
    }
  }
  function uw(n, r, s) {
    n === "focusin" ? (dh(), Vo = r, Bo = s, Vo.attachEvent("onpropertychange", ph)) : n === "focusout" && dh();
  }
  function cw(n) {
    if (n === "selectionchange" || n === "keyup" || n === "keydown") return ma(Bo);
  }
  function fw(n, r) {
    if (n === "click") return ma(r);
  }
  function dw(n, r) {
    if (n === "input" || n === "change") return ma(r);
  }
  function pw(n, r) {
    return n === r && (n !== 0 || 1 / n === 1 / r) || n !== n && r !== r;
  }
  var cn = typeof Object.is == "function" ? Object.is : pw;
  function Ko(n, r) {
    if (cn(n, r)) return !0;
    if (typeof n != "object" || n === null || typeof r != "object" || r === null) return !1;
    var s = Object.keys(n), u = Object.keys(r);
    if (s.length !== u.length) return !1;
    for (u = 0; u < s.length; u++) {
      var p = s[u];
      if (!d.call(r, p) || !cn(n[p], r[p])) return !1;
    }
    return !0;
  }
  function hh(n) {
    for (; n && n.firstChild; ) n = n.firstChild;
    return n;
  }
  function mh(n, r) {
    var s = hh(n);
    n = 0;
    for (var u; s; ) {
      if (s.nodeType === 3) {
        if (u = n + s.textContent.length, n <= r && u >= r) return { node: s, offset: r - n };
        n = u;
      }
      e: {
        for (; s; ) {
          if (s.nextSibling) {
            s = s.nextSibling;
            break e;
          }
          s = s.parentNode;
        }
        s = void 0;
      }
      s = hh(s);
    }
  }
  function yh(n, r) {
    return n && r ? n === r ? !0 : n && n.nodeType === 3 ? !1 : r && r.nodeType === 3 ? yh(n, r.parentNode) : "contains" in n ? n.contains(r) : n.compareDocumentPosition ? !!(n.compareDocumentPosition(r) & 16) : !1 : !1;
  }
  function gh() {
    for (var n = window, r = ot(); r instanceof n.HTMLIFrameElement; ) {
      try {
        var s = typeof r.contentWindow.location.href == "string";
      } catch {
        s = !1;
      }
      if (s) n = r.contentWindow;
      else break;
      r = ot(n.document);
    }
    return r;
  }
  function ju(n) {
    var r = n && n.nodeName && n.nodeName.toLowerCase();
    return r && (r === "input" && (n.type === "text" || n.type === "search" || n.type === "tel" || n.type === "url" || n.type === "password") || r === "textarea" || n.contentEditable === "true");
  }
  function hw(n) {
    var r = gh(), s = n.focusedElem, u = n.selectionRange;
    if (r !== s && s && s.ownerDocument && yh(s.ownerDocument.documentElement, s)) {
      if (u !== null && ju(s)) {
        if (r = u.start, n = u.end, n === void 0 && (n = r), "selectionStart" in s) s.selectionStart = r, s.selectionEnd = Math.min(n, s.value.length);
        else if (n = (r = s.ownerDocument || document) && r.defaultView || window, n.getSelection) {
          n = n.getSelection();
          var p = s.textContent.length, g = Math.min(u.start, p);
          u = u.end === void 0 ? g : Math.min(u.end, p), !n.extend && g > u && (p = u, u = g, g = p), p = mh(s, g);
          var O = mh(
            s,
            u
          );
          p && O && (n.rangeCount !== 1 || n.anchorNode !== p.node || n.anchorOffset !== p.offset || n.focusNode !== O.node || n.focusOffset !== O.offset) && (r = r.createRange(), r.setStart(p.node, p.offset), n.removeAllRanges(), g > u ? (n.addRange(r), n.extend(O.node, O.offset)) : (r.setEnd(O.node, O.offset), n.addRange(r)));
        }
      }
      for (r = [], n = s; n = n.parentNode; ) n.nodeType === 1 && r.push({ element: n, left: n.scrollLeft, top: n.scrollTop });
      for (typeof s.focus == "function" && s.focus(), s = 0; s < r.length; s++) n = r[s], n.element.scrollLeft = n.left, n.element.scrollTop = n.top;
    }
  }
  var mw = f && "documentMode" in document && 11 >= document.documentMode, Fi = null, Au = null, Wo = null, xu = !1;
  function vh(n, r, s) {
    var u = s.window === s ? s.document : s.nodeType === 9 ? s : s.ownerDocument;
    xu || Fi == null || Fi !== ot(u) || (u = Fi, "selectionStart" in u && ju(u) ? u = { start: u.selectionStart, end: u.selectionEnd } : (u = (u.ownerDocument && u.ownerDocument.defaultView || window).getSelection(), u = { anchorNode: u.anchorNode, anchorOffset: u.anchorOffset, focusNode: u.focusNode, focusOffset: u.focusOffset }), Wo && Ko(Wo, u) || (Wo = u, u = _a(Au, "onSelect"), 0 < u.length && (r = new $u("onSelect", "select", null, r, s), n.push({ event: r, listeners: u }), r.target = Fi)));
  }
  function ya(n, r) {
    var s = {};
    return s[n.toLowerCase()] = r.toLowerCase(), s["Webkit" + n] = "webkit" + r, s["Moz" + n] = "moz" + r, s;
  }
  var Ri = { animationend: ya("Animation", "AnimationEnd"), animationiteration: ya("Animation", "AnimationIteration"), animationstart: ya("Animation", "AnimationStart"), transitionend: ya("Transition", "TransitionEnd") }, bu = {}, _h = {};
  f && (_h = document.createElement("div").style, "AnimationEvent" in window || (delete Ri.animationend.animation, delete Ri.animationiteration.animation, delete Ri.animationstart.animation), "TransitionEvent" in window || delete Ri.transitionend.transition);
  function ga(n) {
    if (bu[n]) return bu[n];
    if (!Ri[n]) return n;
    var r = Ri[n], s;
    for (s in r) if (r.hasOwnProperty(s) && s in _h) return bu[n] = r[s];
    return n;
  }
  var Sh = ga("animationend"), wh = ga("animationiteration"), Eh = ga("animationstart"), $h = ga("transitionend"), Oh = /* @__PURE__ */ new Map(), Ph = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
  function hr(n, r) {
    Oh.set(n, r), l(r, [n]);
  }
  for (var Fu = 0; Fu < Ph.length; Fu++) {
    var Ru = Ph[Fu], yw = Ru.toLowerCase(), gw = Ru[0].toUpperCase() + Ru.slice(1);
    hr(yw, "on" + gw);
  }
  hr(Sh, "onAnimationEnd"), hr(wh, "onAnimationIteration"), hr(Eh, "onAnimationStart"), hr("dblclick", "onDoubleClick"), hr("focusin", "onFocus"), hr("focusout", "onBlur"), hr($h, "onTransitionEnd"), c("onMouseEnter", ["mouseout", "mouseover"]), c("onMouseLeave", ["mouseout", "mouseover"]), c("onPointerEnter", ["pointerout", "pointerover"]), c("onPointerLeave", ["pointerout", "pointerover"]), l("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), l("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), l("onBeforeInput", ["compositionend", "keypress", "textInput", "paste"]), l("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), l("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), l("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
  var Ho = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), vw = new Set("cancel close invalid load scroll toggle".split(" ").concat(Ho));
  function Ch(n, r, s) {
    var u = n.type || "unknown-event";
    n.currentTarget = s, yS(u, r, void 0, n), n.currentTarget = null;
  }
  function kh(n, r) {
    r = (r & 4) !== 0;
    for (var s = 0; s < n.length; s++) {
      var u = n[s], p = u.event;
      u = u.listeners;
      e: {
        var g = void 0;
        if (r) for (var O = u.length - 1; 0 <= O; O--) {
          var A = u[O], M = A.instance, Y = A.currentTarget;
          if (A = A.listener, M !== g && p.isPropagationStopped()) break e;
          Ch(p, A, Y), g = M;
        }
        else for (O = 0; O < u.length; O++) {
          if (A = u[O], M = A.instance, Y = A.currentTarget, A = A.listener, M !== g && p.isPropagationStopped()) break e;
          Ch(p, A, Y), g = M;
        }
      }
    }
    if (ta) throw n = pu, ta = !1, pu = null, n;
  }
  function Ye(n, r) {
    var s = r[Ku];
    s === void 0 && (s = r[Ku] = /* @__PURE__ */ new Set());
    var u = n + "__bubble";
    s.has(u) || (Th(r, n, 2, !1), s.add(u));
  }
  function Du(n, r, s) {
    var u = 0;
    r && (u |= 4), Th(s, n, u, r);
  }
  var va = "_reactListening" + Math.random().toString(36).slice(2);
  function qo(n) {
    if (!n[va]) {
      n[va] = !0, o.forEach(function(s) {
        s !== "selectionchange" && (vw.has(s) || Du(s, !1, n), Du(s, !0, n));
      });
      var r = n.nodeType === 9 ? n : n.ownerDocument;
      r === null || r[va] || (r[va] = !0, Du("selectionchange", !1, r));
    }
  }
  function Th(n, r, s, u) {
    switch (Jp(r)) {
      case 1:
        var p = AS;
        break;
      case 4:
        p = xS;
        break;
      default:
        p = Su;
    }
    s = p.bind(null, r, s, n), p = void 0, !du || r !== "touchstart" && r !== "touchmove" && r !== "wheel" || (p = !0), u ? p !== void 0 ? n.addEventListener(r, s, { capture: !0, passive: p }) : n.addEventListener(r, s, !0) : p !== void 0 ? n.addEventListener(r, s, { passive: p }) : n.addEventListener(r, s, !1);
  }
  function Mu(n, r, s, u, p) {
    var g = u;
    if (!(r & 1) && !(r & 2) && u !== null) e: for (; ; ) {
      if (u === null) return;
      var O = u.tag;
      if (O === 3 || O === 4) {
        var A = u.stateNode.containerInfo;
        if (A === p || A.nodeType === 8 && A.parentNode === p) break;
        if (O === 4) for (O = u.return; O !== null; ) {
          var M = O.tag;
          if ((M === 3 || M === 4) && (M = O.stateNode.containerInfo, M === p || M.nodeType === 8 && M.parentNode === p)) return;
          O = O.return;
        }
        for (; A !== null; ) {
          if (O = Gr(A), O === null) return;
          if (M = O.tag, M === 5 || M === 6) {
            u = g = O;
            continue e;
          }
          A = A.parentNode;
        }
      }
      u = u.return;
    }
    xp(function() {
      var Y = g, te = uu(s), oe = [];
      e: {
        var ee = Oh.get(n);
        if (ee !== void 0) {
          var de = $u, ye = n;
          switch (n) {
            case "keypress":
              if (da(s) === 0) break e;
            case "keydown":
            case "keyup":
              de = GS;
              break;
            case "focusin":
              ye = "focus", de = Cu;
              break;
            case "focusout":
              ye = "blur", de = Cu;
              break;
            case "beforeblur":
            case "afterblur":
              de = Cu;
              break;
            case "click":
              if (s.button === 2) break e;
            case "auxclick":
            case "dblclick":
            case "mousedown":
            case "mousemove":
            case "mouseup":
            case "mouseout":
            case "mouseover":
            case "contextmenu":
              de = eh;
              break;
            case "drag":
            case "dragend":
            case "dragenter":
            case "dragexit":
            case "dragleave":
            case "dragover":
            case "dragstart":
            case "drop":
              de = RS;
              break;
            case "touchcancel":
            case "touchend":
            case "touchmove":
            case "touchstart":
              de = JS;
              break;
            case Sh:
            case wh:
            case Eh:
              de = LS;
              break;
            case $h:
              de = ZS;
              break;
            case "scroll":
              de = bS;
              break;
            case "wheel":
              de = tw;
              break;
            case "copy":
            case "cut":
            case "paste":
              de = zS;
              break;
            case "gotpointercapture":
            case "lostpointercapture":
            case "pointercancel":
            case "pointerdown":
            case "pointermove":
            case "pointerout":
            case "pointerover":
            case "pointerup":
              de = nh;
          }
          var ge = (r & 4) !== 0, lt = !ge && n === "scroll", K = ge ? ee !== null ? ee + "Capture" : null : ee;
          ge = [];
          for (var L = Y, W; L !== null; ) {
            W = L;
            var ue = W.stateNode;
            if (W.tag === 5 && ue !== null && (W = ue, K !== null && (ue = No(L, K), ue != null && ge.push(Go(L, ue, W)))), lt) break;
            L = L.return;
          }
          0 < ge.length && (ee = new de(ee, ye, null, s, te), oe.push({ event: ee, listeners: ge }));
        }
      }
      if (!(r & 7)) {
        e: {
          if (ee = n === "mouseover" || n === "pointerover", de = n === "mouseout" || n === "pointerout", ee && s !== lu && (ye = s.relatedTarget || s.fromElement) && (Gr(ye) || ye[Hn])) break e;
          if ((de || ee) && (ee = te.window === te ? te : (ee = te.ownerDocument) ? ee.defaultView || ee.parentWindow : window, de ? (ye = s.relatedTarget || s.toElement, de = Y, ye = ye ? Gr(ye) : null, ye !== null && (lt = qr(ye), ye !== lt || ye.tag !== 5 && ye.tag !== 6) && (ye = null)) : (de = null, ye = Y), de !== ye)) {
            if (ge = eh, ue = "onMouseLeave", K = "onMouseEnter", L = "mouse", (n === "pointerout" || n === "pointerover") && (ge = nh, ue = "onPointerLeave", K = "onPointerEnter", L = "pointer"), lt = de == null ? ee : Li(de), W = ye == null ? ee : Li(ye), ee = new ge(ue, L + "leave", de, s, te), ee.target = lt, ee.relatedTarget = W, ue = null, Gr(te) === Y && (ge = new ge(K, L + "enter", ye, s, te), ge.target = W, ge.relatedTarget = lt, ue = ge), lt = ue, de && ye) t: {
              for (ge = de, K = ye, L = 0, W = ge; W; W = Di(W)) L++;
              for (W = 0, ue = K; ue; ue = Di(ue)) W++;
              for (; 0 < L - W; ) ge = Di(ge), L--;
              for (; 0 < W - L; ) K = Di(K), W--;
              for (; L--; ) {
                if (ge === K || K !== null && ge === K.alternate) break t;
                ge = Di(ge), K = Di(K);
              }
              ge = null;
            }
            else ge = null;
            de !== null && Nh(oe, ee, de, ge, !1), ye !== null && lt !== null && Nh(oe, lt, ye, ge, !0);
          }
        }
        e: {
          if (ee = Y ? Li(Y) : window, de = ee.nodeName && ee.nodeName.toLowerCase(), de === "select" || de === "input" && ee.type === "file") var ve = lw;
          else if (lh(ee)) if (ch) ve = dw;
          else {
            ve = cw;
            var Se = uw;
          }
          else (de = ee.nodeName) && de.toLowerCase() === "input" && (ee.type === "checkbox" || ee.type === "radio") && (ve = fw);
          if (ve && (ve = ve(n, Y))) {
            uh(oe, ve, s, te);
            break e;
          }
          Se && Se(n, ee, Y), n === "focusout" && (Se = ee._wrapperState) && Se.controlled && ee.type === "number" && Wn(ee, "number", ee.value);
        }
        switch (Se = Y ? Li(Y) : window, n) {
          case "focusin":
            (lh(Se) || Se.contentEditable === "true") && (Fi = Se, Au = Y, Wo = null);
            break;
          case "focusout":
            Wo = Au = Fi = null;
            break;
          case "mousedown":
            xu = !0;
            break;
          case "contextmenu":
          case "mouseup":
          case "dragend":
            xu = !1, vh(oe, s, te);
            break;
          case "selectionchange":
            if (mw) break;
          case "keydown":
          case "keyup":
            vh(oe, s, te);
        }
        var we;
        if (Tu) e: {
          switch (n) {
            case "compositionstart":
              var Oe = "onCompositionStart";
              break e;
            case "compositionend":
              Oe = "onCompositionEnd";
              break e;
            case "compositionupdate":
              Oe = "onCompositionUpdate";
              break e;
          }
          Oe = void 0;
        }
        else bi ? sh(n, s) && (Oe = "onCompositionEnd") : n === "keydown" && s.keyCode === 229 && (Oe = "onCompositionStart");
        Oe && (rh && s.locale !== "ko" && (bi || Oe !== "onCompositionStart" ? Oe === "onCompositionEnd" && bi && (we = Xp()) : (pr = te, Eu = "value" in pr ? pr.value : pr.textContent, bi = !0)), Se = _a(Y, Oe), 0 < Se.length && (Oe = new th(Oe, n, null, s, te), oe.push({ event: Oe, listeners: Se }), we ? Oe.data = we : (we = ah(s), we !== null && (Oe.data = we)))), (we = rw ? iw(n, s) : ow(n, s)) && (Y = _a(Y, "onBeforeInput"), 0 < Y.length && (te = new th("onBeforeInput", "beforeinput", null, s, te), oe.push({ event: te, listeners: Y }), te.data = we));
      }
      kh(oe, r);
    });
  }
  function Go(n, r, s) {
    return { instance: n, listener: r, currentTarget: s };
  }
  function _a(n, r) {
    for (var s = r + "Capture", u = []; n !== null; ) {
      var p = n, g = p.stateNode;
      p.tag === 5 && g !== null && (p = g, g = No(n, s), g != null && u.unshift(Go(n, g, p)), g = No(n, r), g != null && u.push(Go(n, g, p))), n = n.return;
    }
    return u;
  }
  function Di(n) {
    if (n === null) return null;
    do
      n = n.return;
    while (n && n.tag !== 5);
    return n || null;
  }
  function Nh(n, r, s, u, p) {
    for (var g = r._reactName, O = []; s !== null && s !== u; ) {
      var A = s, M = A.alternate, Y = A.stateNode;
      if (M !== null && M === u) break;
      A.tag === 5 && Y !== null && (A = Y, p ? (M = No(s, g), M != null && O.unshift(Go(s, M, A))) : p || (M = No(s, g), M != null && O.push(Go(s, M, A)))), s = s.return;
    }
    O.length !== 0 && n.push({ event: r, listeners: O });
  }
  var _w = /\r\n?/g, Sw = /\u0000|\uFFFD/g;
  function Ih(n) {
    return (typeof n == "string" ? n : "" + n).replace(_w, `
`).replace(Sw, "");
  }
  function Sa(n, r, s) {
    if (r = Ih(r), Ih(n) !== r && s) throw Error(i(425));
  }
  function wa() {
  }
  var Lu = null, Uu = null;
  function zu(n, r) {
    return n === "textarea" || n === "noscript" || typeof r.children == "string" || typeof r.children == "number" || typeof r.dangerouslySetInnerHTML == "object" && r.dangerouslySetInnerHTML !== null && r.dangerouslySetInnerHTML.__html != null;
  }
  var Vu = typeof setTimeout == "function" ? setTimeout : void 0, ww = typeof clearTimeout == "function" ? clearTimeout : void 0, jh = typeof Promise == "function" ? Promise : void 0, Ew = typeof queueMicrotask == "function" ? queueMicrotask : typeof jh < "u" ? function(n) {
    return jh.resolve(null).then(n).catch($w);
  } : Vu;
  function $w(n) {
    setTimeout(function() {
      throw n;
    });
  }
  function Bu(n, r) {
    var s = r, u = 0;
    do {
      var p = s.nextSibling;
      if (n.removeChild(s), p && p.nodeType === 8) if (s = p.data, s === "/$") {
        if (u === 0) {
          n.removeChild(p), Mo(r);
          return;
        }
        u--;
      } else s !== "$" && s !== "$?" && s !== "$!" || u++;
      s = p;
    } while (s);
    Mo(r);
  }
  function mr(n) {
    for (; n != null; n = n.nextSibling) {
      var r = n.nodeType;
      if (r === 1 || r === 3) break;
      if (r === 8) {
        if (r = n.data, r === "$" || r === "$!" || r === "$?") break;
        if (r === "/$") return null;
      }
    }
    return n;
  }
  function Ah(n) {
    n = n.previousSibling;
    for (var r = 0; n; ) {
      if (n.nodeType === 8) {
        var s = n.data;
        if (s === "$" || s === "$!" || s === "$?") {
          if (r === 0) return n;
          r--;
        } else s === "/$" && r++;
      }
      n = n.previousSibling;
    }
    return null;
  }
  var Mi = Math.random().toString(36).slice(2), Cn = "__reactFiber$" + Mi, Yo = "__reactProps$" + Mi, Hn = "__reactContainer$" + Mi, Ku = "__reactEvents$" + Mi, Ow = "__reactListeners$" + Mi, Pw = "__reactHandles$" + Mi;
  function Gr(n) {
    var r = n[Cn];
    if (r) return r;
    for (var s = n.parentNode; s; ) {
      if (r = s[Hn] || s[Cn]) {
        if (s = r.alternate, r.child !== null || s !== null && s.child !== null) for (n = Ah(n); n !== null; ) {
          if (s = n[Cn]) return s;
          n = Ah(n);
        }
        return r;
      }
      n = s, s = n.parentNode;
    }
    return null;
  }
  function Qo(n) {
    return n = n[Cn] || n[Hn], !n || n.tag !== 5 && n.tag !== 6 && n.tag !== 13 && n.tag !== 3 ? null : n;
  }
  function Li(n) {
    if (n.tag === 5 || n.tag === 6) return n.stateNode;
    throw Error(i(33));
  }
  function Ea(n) {
    return n[Yo] || null;
  }
  var Wu = [], Ui = -1;
  function yr(n) {
    return { current: n };
  }
  function Qe(n) {
    0 > Ui || (n.current = Wu[Ui], Wu[Ui] = null, Ui--);
  }
  function He(n, r) {
    Ui++, Wu[Ui] = n.current, n.current = r;
  }
  var gr = {}, Ct = yr(gr), Dt = yr(!1), Yr = gr;
  function zi(n, r) {
    var s = n.type.contextTypes;
    if (!s) return gr;
    var u = n.stateNode;
    if (u && u.__reactInternalMemoizedUnmaskedChildContext === r) return u.__reactInternalMemoizedMaskedChildContext;
    var p = {}, g;
    for (g in s) p[g] = r[g];
    return u && (n = n.stateNode, n.__reactInternalMemoizedUnmaskedChildContext = r, n.__reactInternalMemoizedMaskedChildContext = p), p;
  }
  function Mt(n) {
    return n = n.childContextTypes, n != null;
  }
  function $a() {
    Qe(Dt), Qe(Ct);
  }
  function xh(n, r, s) {
    if (Ct.current !== gr) throw Error(i(168));
    He(Ct, r), He(Dt, s);
  }
  function bh(n, r, s) {
    var u = n.stateNode;
    if (r = r.childContextTypes, typeof u.getChildContext != "function") return s;
    u = u.getChildContext();
    for (var p in u) if (!(p in r)) throw Error(i(108, X(n) || "Unknown", p));
    return z({}, s, u);
  }
  function Oa(n) {
    return n = (n = n.stateNode) && n.__reactInternalMemoizedMergedChildContext || gr, Yr = Ct.current, He(Ct, n), He(Dt, Dt.current), !0;
  }
  function Fh(n, r, s) {
    var u = n.stateNode;
    if (!u) throw Error(i(169));
    s ? (n = bh(n, r, Yr), u.__reactInternalMemoizedMergedChildContext = n, Qe(Dt), Qe(Ct), He(Ct, n)) : Qe(Dt), He(Dt, s);
  }
  var qn = null, Pa = !1, Hu = !1;
  function Rh(n) {
    qn === null ? qn = [n] : qn.push(n);
  }
  function Cw(n) {
    Pa = !0, Rh(n);
  }
  function vr() {
    if (!Hu && qn !== null) {
      Hu = !0;
      var n = 0, r = Ve;
      try {
        var s = qn;
        for (Ve = 1; n < s.length; n++) {
          var u = s[n];
          do
            u = u(!0);
          while (u !== null);
        }
        qn = null, Pa = !1;
      } catch (p) {
        throw qn !== null && (qn = qn.slice(n + 1)), Mp(hu, vr), p;
      } finally {
        Ve = r, Hu = !1;
      }
    }
    return null;
  }
  var Vi = [], Bi = 0, Ca = null, ka = 0, Qt = [], Jt = 0, Qr = null, Gn = 1, Yn = "";
  function Jr(n, r) {
    Vi[Bi++] = ka, Vi[Bi++] = Ca, Ca = n, ka = r;
  }
  function Dh(n, r, s) {
    Qt[Jt++] = Gn, Qt[Jt++] = Yn, Qt[Jt++] = Qr, Qr = n;
    var u = Gn;
    n = Yn;
    var p = 32 - un(u) - 1;
    u &= ~(1 << p), s += 1;
    var g = 32 - un(r) + p;
    if (30 < g) {
      var O = p - p % 5;
      g = (u & (1 << O) - 1).toString(32), u >>= O, p -= O, Gn = 1 << 32 - un(r) + p | s << p | u, Yn = g + n;
    } else Gn = 1 << g | s << p | u, Yn = n;
  }
  function qu(n) {
    n.return !== null && (Jr(n, 1), Dh(n, 1, 0));
  }
  function Gu(n) {
    for (; n === Ca; ) Ca = Vi[--Bi], Vi[Bi] = null, ka = Vi[--Bi], Vi[Bi] = null;
    for (; n === Qr; ) Qr = Qt[--Jt], Qt[Jt] = null, Yn = Qt[--Jt], Qt[Jt] = null, Gn = Qt[--Jt], Qt[Jt] = null;
  }
  var qt = null, Gt = null, tt = !1, fn = null;
  function Mh(n, r) {
    var s = tn(5, null, null, 0);
    s.elementType = "DELETED", s.stateNode = r, s.return = n, r = n.deletions, r === null ? (n.deletions = [s], n.flags |= 16) : r.push(s);
  }
  function Lh(n, r) {
    switch (n.tag) {
      case 5:
        var s = n.type;
        return r = r.nodeType !== 1 || s.toLowerCase() !== r.nodeName.toLowerCase() ? null : r, r !== null ? (n.stateNode = r, qt = n, Gt = mr(r.firstChild), !0) : !1;
      case 6:
        return r = n.pendingProps === "" || r.nodeType !== 3 ? null : r, r !== null ? (n.stateNode = r, qt = n, Gt = null, !0) : !1;
      case 13:
        return r = r.nodeType !== 8 ? null : r, r !== null ? (s = Qr !== null ? { id: Gn, overflow: Yn } : null, n.memoizedState = { dehydrated: r, treeContext: s, retryLane: 1073741824 }, s = tn(18, null, null, 0), s.stateNode = r, s.return = n, n.child = s, qt = n, Gt = null, !0) : !1;
      default:
        return !1;
    }
  }
  function Yu(n) {
    return (n.mode & 1) !== 0 && (n.flags & 128) === 0;
  }
  function Qu(n) {
    if (tt) {
      var r = Gt;
      if (r) {
        var s = r;
        if (!Lh(n, r)) {
          if (Yu(n)) throw Error(i(418));
          r = mr(s.nextSibling);
          var u = qt;
          r && Lh(n, r) ? Mh(u, s) : (n.flags = n.flags & -4097 | 2, tt = !1, qt = n);
        }
      } else {
        if (Yu(n)) throw Error(i(418));
        n.flags = n.flags & -4097 | 2, tt = !1, qt = n;
      }
    }
  }
  function Uh(n) {
    for (n = n.return; n !== null && n.tag !== 5 && n.tag !== 3 && n.tag !== 13; ) n = n.return;
    qt = n;
  }
  function Ta(n) {
    if (n !== qt) return !1;
    if (!tt) return Uh(n), tt = !0, !1;
    var r;
    if ((r = n.tag !== 3) && !(r = n.tag !== 5) && (r = n.type, r = r !== "head" && r !== "body" && !zu(n.type, n.memoizedProps)), r && (r = Gt)) {
      if (Yu(n)) throw zh(), Error(i(418));
      for (; r; ) Mh(n, r), r = mr(r.nextSibling);
    }
    if (Uh(n), n.tag === 13) {
      if (n = n.memoizedState, n = n !== null ? n.dehydrated : null, !n) throw Error(i(317));
      e: {
        for (n = n.nextSibling, r = 0; n; ) {
          if (n.nodeType === 8) {
            var s = n.data;
            if (s === "/$") {
              if (r === 0) {
                Gt = mr(n.nextSibling);
                break e;
              }
              r--;
            } else s !== "$" && s !== "$!" && s !== "$?" || r++;
          }
          n = n.nextSibling;
        }
        Gt = null;
      }
    } else Gt = qt ? mr(n.stateNode.nextSibling) : null;
    return !0;
  }
  function zh() {
    for (var n = Gt; n; ) n = mr(n.nextSibling);
  }
  function Ki() {
    Gt = qt = null, tt = !1;
  }
  function Ju(n) {
    fn === null ? fn = [n] : fn.push(n);
  }
  var kw = T.ReactCurrentBatchConfig;
  function Jo(n, r, s) {
    if (n = s.ref, n !== null && typeof n != "function" && typeof n != "object") {
      if (s._owner) {
        if (s = s._owner, s) {
          if (s.tag !== 1) throw Error(i(309));
          var u = s.stateNode;
        }
        if (!u) throw Error(i(147, n));
        var p = u, g = "" + n;
        return r !== null && r.ref !== null && typeof r.ref == "function" && r.ref._stringRef === g ? r.ref : (r = function(O) {
          var A = p.refs;
          O === null ? delete A[g] : A[g] = O;
        }, r._stringRef = g, r);
      }
      if (typeof n != "string") throw Error(i(284));
      if (!s._owner) throw Error(i(290, n));
    }
    return n;
  }
  function Na(n, r) {
    throw n = Object.prototype.toString.call(r), Error(i(31, n === "[object Object]" ? "object with keys {" + Object.keys(r).join(", ") + "}" : n));
  }
  function Vh(n) {
    var r = n._init;
    return r(n._payload);
  }
  function Bh(n) {
    function r(K, L) {
      if (n) {
        var W = K.deletions;
        W === null ? (K.deletions = [L], K.flags |= 16) : W.push(L);
      }
    }
    function s(K, L) {
      if (!n) return null;
      for (; L !== null; ) r(K, L), L = L.sibling;
      return null;
    }
    function u(K, L) {
      for (K = /* @__PURE__ */ new Map(); L !== null; ) L.key !== null ? K.set(L.key, L) : K.set(L.index, L), L = L.sibling;
      return K;
    }
    function p(K, L) {
      return K = Cr(K, L), K.index = 0, K.sibling = null, K;
    }
    function g(K, L, W) {
      return K.index = W, n ? (W = K.alternate, W !== null ? (W = W.index, W < L ? (K.flags |= 2, L) : W) : (K.flags |= 2, L)) : (K.flags |= 1048576, L);
    }
    function O(K) {
      return n && K.alternate === null && (K.flags |= 2), K;
    }
    function A(K, L, W, ue) {
      return L === null || L.tag !== 6 ? (L = Vc(W, K.mode, ue), L.return = K, L) : (L = p(L, W), L.return = K, L);
    }
    function M(K, L, W, ue) {
      var ve = W.type;
      return ve === F ? te(K, L, W.props.children, ue, W.key) : L !== null && (L.elementType === ve || typeof ve == "object" && ve !== null && ve.$$typeof === ne && Vh(ve) === L.type) ? (ue = p(L, W.props), ue.ref = Jo(K, L, W), ue.return = K, ue) : (ue = Za(W.type, W.key, W.props, null, K.mode, ue), ue.ref = Jo(K, L, W), ue.return = K, ue);
    }
    function Y(K, L, W, ue) {
      return L === null || L.tag !== 4 || L.stateNode.containerInfo !== W.containerInfo || L.stateNode.implementation !== W.implementation ? (L = Bc(W, K.mode, ue), L.return = K, L) : (L = p(L, W.children || []), L.return = K, L);
    }
    function te(K, L, W, ue, ve) {
      return L === null || L.tag !== 7 ? (L = oi(W, K.mode, ue, ve), L.return = K, L) : (L = p(L, W), L.return = K, L);
    }
    function oe(K, L, W) {
      if (typeof L == "string" && L !== "" || typeof L == "number") return L = Vc("" + L, K.mode, W), L.return = K, L;
      if (typeof L == "object" && L !== null) {
        switch (L.$$typeof) {
          case N:
            return W = Za(L.type, L.key, L.props, null, K.mode, W), W.ref = Jo(K, null, L), W.return = K, W;
          case x:
            return L = Bc(L, K.mode, W), L.return = K, L;
          case ne:
            var ue = L._init;
            return oe(K, ue(L._payload), W);
        }
        if ($n(L) || ae(L)) return L = oi(L, K.mode, W, null), L.return = K, L;
        Na(K, L);
      }
      return null;
    }
    function ee(K, L, W, ue) {
      var ve = L !== null ? L.key : null;
      if (typeof W == "string" && W !== "" || typeof W == "number") return ve !== null ? null : A(K, L, "" + W, ue);
      if (typeof W == "object" && W !== null) {
        switch (W.$$typeof) {
          case N:
            return W.key === ve ? M(K, L, W, ue) : null;
          case x:
            return W.key === ve ? Y(K, L, W, ue) : null;
          case ne:
            return ve = W._init, ee(
              K,
              L,
              ve(W._payload),
              ue
            );
        }
        if ($n(W) || ae(W)) return ve !== null ? null : te(K, L, W, ue, null);
        Na(K, W);
      }
      return null;
    }
    function de(K, L, W, ue, ve) {
      if (typeof ue == "string" && ue !== "" || typeof ue == "number") return K = K.get(W) || null, A(L, K, "" + ue, ve);
      if (typeof ue == "object" && ue !== null) {
        switch (ue.$$typeof) {
          case N:
            return K = K.get(ue.key === null ? W : ue.key) || null, M(L, K, ue, ve);
          case x:
            return K = K.get(ue.key === null ? W : ue.key) || null, Y(L, K, ue, ve);
          case ne:
            var Se = ue._init;
            return de(K, L, W, Se(ue._payload), ve);
        }
        if ($n(ue) || ae(ue)) return K = K.get(W) || null, te(L, K, ue, ve, null);
        Na(L, ue);
      }
      return null;
    }
    function ye(K, L, W, ue) {
      for (var ve = null, Se = null, we = L, Oe = L = 0, _t = null; we !== null && Oe < W.length; Oe++) {
        we.index > Oe ? (_t = we, we = null) : _t = we.sibling;
        var De = ee(K, we, W[Oe], ue);
        if (De === null) {
          we === null && (we = _t);
          break;
        }
        n && we && De.alternate === null && r(K, we), L = g(De, L, Oe), Se === null ? ve = De : Se.sibling = De, Se = De, we = _t;
      }
      if (Oe === W.length) return s(K, we), tt && Jr(K, Oe), ve;
      if (we === null) {
        for (; Oe < W.length; Oe++) we = oe(K, W[Oe], ue), we !== null && (L = g(we, L, Oe), Se === null ? ve = we : Se.sibling = we, Se = we);
        return tt && Jr(K, Oe), ve;
      }
      for (we = u(K, we); Oe < W.length; Oe++) _t = de(we, K, Oe, W[Oe], ue), _t !== null && (n && _t.alternate !== null && we.delete(_t.key === null ? Oe : _t.key), L = g(_t, L, Oe), Se === null ? ve = _t : Se.sibling = _t, Se = _t);
      return n && we.forEach(function(kr) {
        return r(K, kr);
      }), tt && Jr(K, Oe), ve;
    }
    function ge(K, L, W, ue) {
      var ve = ae(W);
      if (typeof ve != "function") throw Error(i(150));
      if (W = ve.call(W), W == null) throw Error(i(151));
      for (var Se = ve = null, we = L, Oe = L = 0, _t = null, De = W.next(); we !== null && !De.done; Oe++, De = W.next()) {
        we.index > Oe ? (_t = we, we = null) : _t = we.sibling;
        var kr = ee(K, we, De.value, ue);
        if (kr === null) {
          we === null && (we = _t);
          break;
        }
        n && we && kr.alternate === null && r(K, we), L = g(kr, L, Oe), Se === null ? ve = kr : Se.sibling = kr, Se = kr, we = _t;
      }
      if (De.done) return s(
        K,
        we
      ), tt && Jr(K, Oe), ve;
      if (we === null) {
        for (; !De.done; Oe++, De = W.next()) De = oe(K, De.value, ue), De !== null && (L = g(De, L, Oe), Se === null ? ve = De : Se.sibling = De, Se = De);
        return tt && Jr(K, Oe), ve;
      }
      for (we = u(K, we); !De.done; Oe++, De = W.next()) De = de(we, K, Oe, De.value, ue), De !== null && (n && De.alternate !== null && we.delete(De.key === null ? Oe : De.key), L = g(De, L, Oe), Se === null ? ve = De : Se.sibling = De, Se = De);
      return n && we.forEach(function(s1) {
        return r(K, s1);
      }), tt && Jr(K, Oe), ve;
    }
    function lt(K, L, W, ue) {
      if (typeof W == "object" && W !== null && W.type === F && W.key === null && (W = W.props.children), typeof W == "object" && W !== null) {
        switch (W.$$typeof) {
          case N:
            e: {
              for (var ve = W.key, Se = L; Se !== null; ) {
                if (Se.key === ve) {
                  if (ve = W.type, ve === F) {
                    if (Se.tag === 7) {
                      s(K, Se.sibling), L = p(Se, W.props.children), L.return = K, K = L;
                      break e;
                    }
                  } else if (Se.elementType === ve || typeof ve == "object" && ve !== null && ve.$$typeof === ne && Vh(ve) === Se.type) {
                    s(K, Se.sibling), L = p(Se, W.props), L.ref = Jo(K, Se, W), L.return = K, K = L;
                    break e;
                  }
                  s(K, Se);
                  break;
                } else r(K, Se);
                Se = Se.sibling;
              }
              W.type === F ? (L = oi(W.props.children, K.mode, ue, W.key), L.return = K, K = L) : (ue = Za(W.type, W.key, W.props, null, K.mode, ue), ue.ref = Jo(K, L, W), ue.return = K, K = ue);
            }
            return O(K);
          case x:
            e: {
              for (Se = W.key; L !== null; ) {
                if (L.key === Se) if (L.tag === 4 && L.stateNode.containerInfo === W.containerInfo && L.stateNode.implementation === W.implementation) {
                  s(K, L.sibling), L = p(L, W.children || []), L.return = K, K = L;
                  break e;
                } else {
                  s(K, L);
                  break;
                }
                else r(K, L);
                L = L.sibling;
              }
              L = Bc(W, K.mode, ue), L.return = K, K = L;
            }
            return O(K);
          case ne:
            return Se = W._init, lt(K, L, Se(W._payload), ue);
        }
        if ($n(W)) return ye(K, L, W, ue);
        if (ae(W)) return ge(K, L, W, ue);
        Na(K, W);
      }
      return typeof W == "string" && W !== "" || typeof W == "number" ? (W = "" + W, L !== null && L.tag === 6 ? (s(K, L.sibling), L = p(L, W), L.return = K, K = L) : (s(K, L), L = Vc(W, K.mode, ue), L.return = K, K = L), O(K)) : s(K, L);
    }
    return lt;
  }
  var Wi = Bh(!0), Kh = Bh(!1), Ia = yr(null), ja = null, Hi = null, Xu = null;
  function Zu() {
    Xu = Hi = ja = null;
  }
  function ec(n) {
    var r = Ia.current;
    Qe(Ia), n._currentValue = r;
  }
  function tc(n, r, s) {
    for (; n !== null; ) {
      var u = n.alternate;
      if ((n.childLanes & r) !== r ? (n.childLanes |= r, u !== null && (u.childLanes |= r)) : u !== null && (u.childLanes & r) !== r && (u.childLanes |= r), n === s) break;
      n = n.return;
    }
  }
  function qi(n, r) {
    ja = n, Xu = Hi = null, n = n.dependencies, n !== null && n.firstContext !== null && (n.lanes & r && (Lt = !0), n.firstContext = null);
  }
  function Xt(n) {
    var r = n._currentValue;
    if (Xu !== n) if (n = { context: n, memoizedValue: r, next: null }, Hi === null) {
      if (ja === null) throw Error(i(308));
      Hi = n, ja.dependencies = { lanes: 0, firstContext: n };
    } else Hi = Hi.next = n;
    return r;
  }
  var Xr = null;
  function nc(n) {
    Xr === null ? Xr = [n] : Xr.push(n);
  }
  function Wh(n, r, s, u) {
    var p = r.interleaved;
    return p === null ? (s.next = s, nc(r)) : (s.next = p.next, p.next = s), r.interleaved = s, Qn(n, u);
  }
  function Qn(n, r) {
    n.lanes |= r;
    var s = n.alternate;
    for (s !== null && (s.lanes |= r), s = n, n = n.return; n !== null; ) n.childLanes |= r, s = n.alternate, s !== null && (s.childLanes |= r), s = n, n = n.return;
    return s.tag === 3 ? s.stateNode : null;
  }
  var _r = !1;
  function rc(n) {
    n.updateQueue = { baseState: n.memoizedState, firstBaseUpdate: null, lastBaseUpdate: null, shared: { pending: null, interleaved: null, lanes: 0 }, effects: null };
  }
  function Hh(n, r) {
    n = n.updateQueue, r.updateQueue === n && (r.updateQueue = { baseState: n.baseState, firstBaseUpdate: n.firstBaseUpdate, lastBaseUpdate: n.lastBaseUpdate, shared: n.shared, effects: n.effects });
  }
  function Jn(n, r) {
    return { eventTime: n, lane: r, tag: 0, payload: null, callback: null, next: null };
  }
  function Sr(n, r, s) {
    var u = n.updateQueue;
    if (u === null) return null;
    if (u = u.shared, Re & 2) {
      var p = u.pending;
      return p === null ? r.next = r : (r.next = p.next, p.next = r), u.pending = r, Qn(n, s);
    }
    return p = u.interleaved, p === null ? (r.next = r, nc(u)) : (r.next = p.next, p.next = r), u.interleaved = r, Qn(n, s);
  }
  function Aa(n, r, s) {
    if (r = r.updateQueue, r !== null && (r = r.shared, (s & 4194240) !== 0)) {
      var u = r.lanes;
      u &= n.pendingLanes, s |= u, r.lanes = s, gu(n, s);
    }
  }
  function qh(n, r) {
    var s = n.updateQueue, u = n.alternate;
    if (u !== null && (u = u.updateQueue, s === u)) {
      var p = null, g = null;
      if (s = s.firstBaseUpdate, s !== null) {
        do {
          var O = { eventTime: s.eventTime, lane: s.lane, tag: s.tag, payload: s.payload, callback: s.callback, next: null };
          g === null ? p = g = O : g = g.next = O, s = s.next;
        } while (s !== null);
        g === null ? p = g = r : g = g.next = r;
      } else p = g = r;
      s = { baseState: u.baseState, firstBaseUpdate: p, lastBaseUpdate: g, shared: u.shared, effects: u.effects }, n.updateQueue = s;
      return;
    }
    n = s.lastBaseUpdate, n === null ? s.firstBaseUpdate = r : n.next = r, s.lastBaseUpdate = r;
  }
  function xa(n, r, s, u) {
    var p = n.updateQueue;
    _r = !1;
    var g = p.firstBaseUpdate, O = p.lastBaseUpdate, A = p.shared.pending;
    if (A !== null) {
      p.shared.pending = null;
      var M = A, Y = M.next;
      M.next = null, O === null ? g = Y : O.next = Y, O = M;
      var te = n.alternate;
      te !== null && (te = te.updateQueue, A = te.lastBaseUpdate, A !== O && (A === null ? te.firstBaseUpdate = Y : A.next = Y, te.lastBaseUpdate = M));
    }
    if (g !== null) {
      var oe = p.baseState;
      O = 0, te = Y = M = null, A = g;
      do {
        var ee = A.lane, de = A.eventTime;
        if ((u & ee) === ee) {
          te !== null && (te = te.next = {
            eventTime: de,
            lane: 0,
            tag: A.tag,
            payload: A.payload,
            callback: A.callback,
            next: null
          });
          e: {
            var ye = n, ge = A;
            switch (ee = r, de = s, ge.tag) {
              case 1:
                if (ye = ge.payload, typeof ye == "function") {
                  oe = ye.call(de, oe, ee);
                  break e;
                }
                oe = ye;
                break e;
              case 3:
                ye.flags = ye.flags & -65537 | 128;
              case 0:
                if (ye = ge.payload, ee = typeof ye == "function" ? ye.call(de, oe, ee) : ye, ee == null) break e;
                oe = z({}, oe, ee);
                break e;
              case 2:
                _r = !0;
            }
          }
          A.callback !== null && A.lane !== 0 && (n.flags |= 64, ee = p.effects, ee === null ? p.effects = [A] : ee.push(A));
        } else de = { eventTime: de, lane: ee, tag: A.tag, payload: A.payload, callback: A.callback, next: null }, te === null ? (Y = te = de, M = oe) : te = te.next = de, O |= ee;
        if (A = A.next, A === null) {
          if (A = p.shared.pending, A === null) break;
          ee = A, A = ee.next, ee.next = null, p.lastBaseUpdate = ee, p.shared.pending = null;
        }
      } while (!0);
      if (te === null && (M = oe), p.baseState = M, p.firstBaseUpdate = Y, p.lastBaseUpdate = te, r = p.shared.interleaved, r !== null) {
        p = r;
        do
          O |= p.lane, p = p.next;
        while (p !== r);
      } else g === null && (p.shared.lanes = 0);
      ti |= O, n.lanes = O, n.memoizedState = oe;
    }
  }
  function Gh(n, r, s) {
    if (n = r.effects, r.effects = null, n !== null) for (r = 0; r < n.length; r++) {
      var u = n[r], p = u.callback;
      if (p !== null) {
        if (u.callback = null, u = s, typeof p != "function") throw Error(i(191, p));
        p.call(u);
      }
    }
  }
  var Xo = {}, kn = yr(Xo), Zo = yr(Xo), es = yr(Xo);
  function Zr(n) {
    if (n === Xo) throw Error(i(174));
    return n;
  }
  function ic(n, r) {
    switch (He(es, r), He(Zo, n), He(kn, Xo), n = r.nodeType, n) {
      case 9:
      case 11:
        r = (r = r.documentElement) ? r.namespaceURI : Kr(null, "");
        break;
      default:
        n = n === 8 ? r.parentNode : r, r = n.namespaceURI || null, n = n.tagName, r = Kr(r, n);
    }
    Qe(kn), He(kn, r);
  }
  function Gi() {
    Qe(kn), Qe(Zo), Qe(es);
  }
  function Yh(n) {
    Zr(es.current);
    var r = Zr(kn.current), s = Kr(r, n.type);
    r !== s && (He(Zo, n), He(kn, s));
  }
  function oc(n) {
    Zo.current === n && (Qe(kn), Qe(Zo));
  }
  var rt = yr(0);
  function ba(n) {
    for (var r = n; r !== null; ) {
      if (r.tag === 13) {
        var s = r.memoizedState;
        if (s !== null && (s = s.dehydrated, s === null || s.data === "$?" || s.data === "$!")) return r;
      } else if (r.tag === 19 && r.memoizedProps.revealOrder !== void 0) {
        if (r.flags & 128) return r;
      } else if (r.child !== null) {
        r.child.return = r, r = r.child;
        continue;
      }
      if (r === n) break;
      for (; r.sibling === null; ) {
        if (r.return === null || r.return === n) return null;
        r = r.return;
      }
      r.sibling.return = r.return, r = r.sibling;
    }
    return null;
  }
  var sc = [];
  function ac() {
    for (var n = 0; n < sc.length; n++) sc[n]._workInProgressVersionPrimary = null;
    sc.length = 0;
  }
  var Fa = T.ReactCurrentDispatcher, lc = T.ReactCurrentBatchConfig, ei = 0, it = null, pt = null, gt = null, Ra = !1, ts = !1, ns = 0, Tw = 0;
  function kt() {
    throw Error(i(321));
  }
  function uc(n, r) {
    if (r === null) return !1;
    for (var s = 0; s < r.length && s < n.length; s++) if (!cn(n[s], r[s])) return !1;
    return !0;
  }
  function cc(n, r, s, u, p, g) {
    if (ei = g, it = r, r.memoizedState = null, r.updateQueue = null, r.lanes = 0, Fa.current = n === null || n.memoizedState === null ? Aw : xw, n = s(u, p), ts) {
      g = 0;
      do {
        if (ts = !1, ns = 0, 25 <= g) throw Error(i(301));
        g += 1, gt = pt = null, r.updateQueue = null, Fa.current = bw, n = s(u, p);
      } while (ts);
    }
    if (Fa.current = La, r = pt !== null && pt.next !== null, ei = 0, gt = pt = it = null, Ra = !1, r) throw Error(i(300));
    return n;
  }
  function fc() {
    var n = ns !== 0;
    return ns = 0, n;
  }
  function Tn() {
    var n = { memoizedState: null, baseState: null, baseQueue: null, queue: null, next: null };
    return gt === null ? it.memoizedState = gt = n : gt = gt.next = n, gt;
  }
  function Zt() {
    if (pt === null) {
      var n = it.alternate;
      n = n !== null ? n.memoizedState : null;
    } else n = pt.next;
    var r = gt === null ? it.memoizedState : gt.next;
    if (r !== null) gt = r, pt = n;
    else {
      if (n === null) throw Error(i(310));
      pt = n, n = { memoizedState: pt.memoizedState, baseState: pt.baseState, baseQueue: pt.baseQueue, queue: pt.queue, next: null }, gt === null ? it.memoizedState = gt = n : gt = gt.next = n;
    }
    return gt;
  }
  function rs(n, r) {
    return typeof r == "function" ? r(n) : r;
  }
  function dc(n) {
    var r = Zt(), s = r.queue;
    if (s === null) throw Error(i(311));
    s.lastRenderedReducer = n;
    var u = pt, p = u.baseQueue, g = s.pending;
    if (g !== null) {
      if (p !== null) {
        var O = p.next;
        p.next = g.next, g.next = O;
      }
      u.baseQueue = p = g, s.pending = null;
    }
    if (p !== null) {
      g = p.next, u = u.baseState;
      var A = O = null, M = null, Y = g;
      do {
        var te = Y.lane;
        if ((ei & te) === te) M !== null && (M = M.next = { lane: 0, action: Y.action, hasEagerState: Y.hasEagerState, eagerState: Y.eagerState, next: null }), u = Y.hasEagerState ? Y.eagerState : n(u, Y.action);
        else {
          var oe = {
            lane: te,
            action: Y.action,
            hasEagerState: Y.hasEagerState,
            eagerState: Y.eagerState,
            next: null
          };
          M === null ? (A = M = oe, O = u) : M = M.next = oe, it.lanes |= te, ti |= te;
        }
        Y = Y.next;
      } while (Y !== null && Y !== g);
      M === null ? O = u : M.next = A, cn(u, r.memoizedState) || (Lt = !0), r.memoizedState = u, r.baseState = O, r.baseQueue = M, s.lastRenderedState = u;
    }
    if (n = s.interleaved, n !== null) {
      p = n;
      do
        g = p.lane, it.lanes |= g, ti |= g, p = p.next;
      while (p !== n);
    } else p === null && (s.lanes = 0);
    return [r.memoizedState, s.dispatch];
  }
  function pc(n) {
    var r = Zt(), s = r.queue;
    if (s === null) throw Error(i(311));
    s.lastRenderedReducer = n;
    var u = s.dispatch, p = s.pending, g = r.memoizedState;
    if (p !== null) {
      s.pending = null;
      var O = p = p.next;
      do
        g = n(g, O.action), O = O.next;
      while (O !== p);
      cn(g, r.memoizedState) || (Lt = !0), r.memoizedState = g, r.baseQueue === null && (r.baseState = g), s.lastRenderedState = g;
    }
    return [g, u];
  }
  function Qh() {
  }
  function Jh(n, r) {
    var s = it, u = Zt(), p = r(), g = !cn(u.memoizedState, p);
    if (g && (u.memoizedState = p, Lt = !0), u = u.queue, hc(em.bind(null, s, u, n), [n]), u.getSnapshot !== r || g || gt !== null && gt.memoizedState.tag & 1) {
      if (s.flags |= 2048, is(9, Zh.bind(null, s, u, p, r), void 0, null), vt === null) throw Error(i(349));
      ei & 30 || Xh(s, r, p);
    }
    return p;
  }
  function Xh(n, r, s) {
    n.flags |= 16384, n = { getSnapshot: r, value: s }, r = it.updateQueue, r === null ? (r = { lastEffect: null, stores: null }, it.updateQueue = r, r.stores = [n]) : (s = r.stores, s === null ? r.stores = [n] : s.push(n));
  }
  function Zh(n, r, s, u) {
    r.value = s, r.getSnapshot = u, tm(r) && nm(n);
  }
  function em(n, r, s) {
    return s(function() {
      tm(r) && nm(n);
    });
  }
  function tm(n) {
    var r = n.getSnapshot;
    n = n.value;
    try {
      var s = r();
      return !cn(n, s);
    } catch {
      return !0;
    }
  }
  function nm(n) {
    var r = Qn(n, 1);
    r !== null && mn(r, n, 1, -1);
  }
  function rm(n) {
    var r = Tn();
    return typeof n == "function" && (n = n()), r.memoizedState = r.baseState = n, n = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: rs, lastRenderedState: n }, r.queue = n, n = n.dispatch = jw.bind(null, it, n), [r.memoizedState, n];
  }
  function is(n, r, s, u) {
    return n = { tag: n, create: r, destroy: s, deps: u, next: null }, r = it.updateQueue, r === null ? (r = { lastEffect: null, stores: null }, it.updateQueue = r, r.lastEffect = n.next = n) : (s = r.lastEffect, s === null ? r.lastEffect = n.next = n : (u = s.next, s.next = n, n.next = u, r.lastEffect = n)), n;
  }
  function im() {
    return Zt().memoizedState;
  }
  function Da(n, r, s, u) {
    var p = Tn();
    it.flags |= n, p.memoizedState = is(1 | r, s, void 0, u === void 0 ? null : u);
  }
  function Ma(n, r, s, u) {
    var p = Zt();
    u = u === void 0 ? null : u;
    var g = void 0;
    if (pt !== null) {
      var O = pt.memoizedState;
      if (g = O.destroy, u !== null && uc(u, O.deps)) {
        p.memoizedState = is(r, s, g, u);
        return;
      }
    }
    it.flags |= n, p.memoizedState = is(1 | r, s, g, u);
  }
  function om(n, r) {
    return Da(8390656, 8, n, r);
  }
  function hc(n, r) {
    return Ma(2048, 8, n, r);
  }
  function sm(n, r) {
    return Ma(4, 2, n, r);
  }
  function am(n, r) {
    return Ma(4, 4, n, r);
  }
  function lm(n, r) {
    if (typeof r == "function") return n = n(), r(n), function() {
      r(null);
    };
    if (r != null) return n = n(), r.current = n, function() {
      r.current = null;
    };
  }
  function um(n, r, s) {
    return s = s != null ? s.concat([n]) : null, Ma(4, 4, lm.bind(null, r, n), s);
  }
  function mc() {
  }
  function cm(n, r) {
    var s = Zt();
    r = r === void 0 ? null : r;
    var u = s.memoizedState;
    return u !== null && r !== null && uc(r, u[1]) ? u[0] : (s.memoizedState = [n, r], n);
  }
  function fm(n, r) {
    var s = Zt();
    r = r === void 0 ? null : r;
    var u = s.memoizedState;
    return u !== null && r !== null && uc(r, u[1]) ? u[0] : (n = n(), s.memoizedState = [n, r], n);
  }
  function dm(n, r, s) {
    return ei & 21 ? (cn(s, r) || (s = Vp(), it.lanes |= s, ti |= s, n.baseState = !0), r) : (n.baseState && (n.baseState = !1, Lt = !0), n.memoizedState = s);
  }
  function Nw(n, r) {
    var s = Ve;
    Ve = s !== 0 && 4 > s ? s : 4, n(!0);
    var u = lc.transition;
    lc.transition = {};
    try {
      n(!1), r();
    } finally {
      Ve = s, lc.transition = u;
    }
  }
  function pm() {
    return Zt().memoizedState;
  }
  function Iw(n, r, s) {
    var u = Or(n);
    if (s = { lane: u, action: s, hasEagerState: !1, eagerState: null, next: null }, hm(n)) mm(r, s);
    else if (s = Wh(n, r, s, u), s !== null) {
      var p = xt();
      mn(s, n, u, p), ym(s, r, u);
    }
  }
  function jw(n, r, s) {
    var u = Or(n), p = { lane: u, action: s, hasEagerState: !1, eagerState: null, next: null };
    if (hm(n)) mm(r, p);
    else {
      var g = n.alternate;
      if (n.lanes === 0 && (g === null || g.lanes === 0) && (g = r.lastRenderedReducer, g !== null)) try {
        var O = r.lastRenderedState, A = g(O, s);
        if (p.hasEagerState = !0, p.eagerState = A, cn(A, O)) {
          var M = r.interleaved;
          M === null ? (p.next = p, nc(r)) : (p.next = M.next, M.next = p), r.interleaved = p;
          return;
        }
      } catch {
      } finally {
      }
      s = Wh(n, r, p, u), s !== null && (p = xt(), mn(s, n, u, p), ym(s, r, u));
    }
  }
  function hm(n) {
    var r = n.alternate;
    return n === it || r !== null && r === it;
  }
  function mm(n, r) {
    ts = Ra = !0;
    var s = n.pending;
    s === null ? r.next = r : (r.next = s.next, s.next = r), n.pending = r;
  }
  function ym(n, r, s) {
    if (s & 4194240) {
      var u = r.lanes;
      u &= n.pendingLanes, s |= u, r.lanes = s, gu(n, s);
    }
  }
  var La = { readContext: Xt, useCallback: kt, useContext: kt, useEffect: kt, useImperativeHandle: kt, useInsertionEffect: kt, useLayoutEffect: kt, useMemo: kt, useReducer: kt, useRef: kt, useState: kt, useDebugValue: kt, useDeferredValue: kt, useTransition: kt, useMutableSource: kt, useSyncExternalStore: kt, useId: kt, unstable_isNewReconciler: !1 }, Aw = { readContext: Xt, useCallback: function(n, r) {
    return Tn().memoizedState = [n, r === void 0 ? null : r], n;
  }, useContext: Xt, useEffect: om, useImperativeHandle: function(n, r, s) {
    return s = s != null ? s.concat([n]) : null, Da(
      4194308,
      4,
      lm.bind(null, r, n),
      s
    );
  }, useLayoutEffect: function(n, r) {
    return Da(4194308, 4, n, r);
  }, useInsertionEffect: function(n, r) {
    return Da(4, 2, n, r);
  }, useMemo: function(n, r) {
    var s = Tn();
    return r = r === void 0 ? null : r, n = n(), s.memoizedState = [n, r], n;
  }, useReducer: function(n, r, s) {
    var u = Tn();
    return r = s !== void 0 ? s(r) : r, u.memoizedState = u.baseState = r, n = { pending: null, interleaved: null, lanes: 0, dispatch: null, lastRenderedReducer: n, lastRenderedState: r }, u.queue = n, n = n.dispatch = Iw.bind(null, it, n), [u.memoizedState, n];
  }, useRef: function(n) {
    var r = Tn();
    return n = { current: n }, r.memoizedState = n;
  }, useState: rm, useDebugValue: mc, useDeferredValue: function(n) {
    return Tn().memoizedState = n;
  }, useTransition: function() {
    var n = rm(!1), r = n[0];
    return n = Nw.bind(null, n[1]), Tn().memoizedState = n, [r, n];
  }, useMutableSource: function() {
  }, useSyncExternalStore: function(n, r, s) {
    var u = it, p = Tn();
    if (tt) {
      if (s === void 0) throw Error(i(407));
      s = s();
    } else {
      if (s = r(), vt === null) throw Error(i(349));
      ei & 30 || Xh(u, r, s);
    }
    p.memoizedState = s;
    var g = { value: s, getSnapshot: r };
    return p.queue = g, om(em.bind(
      null,
      u,
      g,
      n
    ), [n]), u.flags |= 2048, is(9, Zh.bind(null, u, g, s, r), void 0, null), s;
  }, useId: function() {
    var n = Tn(), r = vt.identifierPrefix;
    if (tt) {
      var s = Yn, u = Gn;
      s = (u & ~(1 << 32 - un(u) - 1)).toString(32) + s, r = ":" + r + "R" + s, s = ns++, 0 < s && (r += "H" + s.toString(32)), r += ":";
    } else s = Tw++, r = ":" + r + "r" + s.toString(32) + ":";
    return n.memoizedState = r;
  }, unstable_isNewReconciler: !1 }, xw = {
    readContext: Xt,
    useCallback: cm,
    useContext: Xt,
    useEffect: hc,
    useImperativeHandle: um,
    useInsertionEffect: sm,
    useLayoutEffect: am,
    useMemo: fm,
    useReducer: dc,
    useRef: im,
    useState: function() {
      return dc(rs);
    },
    useDebugValue: mc,
    useDeferredValue: function(n) {
      var r = Zt();
      return dm(r, pt.memoizedState, n);
    },
    useTransition: function() {
      var n = dc(rs)[0], r = Zt().memoizedState;
      return [n, r];
    },
    useMutableSource: Qh,
    useSyncExternalStore: Jh,
    useId: pm,
    unstable_isNewReconciler: !1
  }, bw = { readContext: Xt, useCallback: cm, useContext: Xt, useEffect: hc, useImperativeHandle: um, useInsertionEffect: sm, useLayoutEffect: am, useMemo: fm, useReducer: pc, useRef: im, useState: function() {
    return pc(rs);
  }, useDebugValue: mc, useDeferredValue: function(n) {
    var r = Zt();
    return pt === null ? r.memoizedState = n : dm(r, pt.memoizedState, n);
  }, useTransition: function() {
    var n = pc(rs)[0], r = Zt().memoizedState;
    return [n, r];
  }, useMutableSource: Qh, useSyncExternalStore: Jh, useId: pm, unstable_isNewReconciler: !1 };
  function dn(n, r) {
    if (n && n.defaultProps) {
      r = z({}, r), n = n.defaultProps;
      for (var s in n) r[s] === void 0 && (r[s] = n[s]);
      return r;
    }
    return r;
  }
  function yc(n, r, s, u) {
    r = n.memoizedState, s = s(u, r), s = s == null ? r : z({}, r, s), n.memoizedState = s, n.lanes === 0 && (n.updateQueue.baseState = s);
  }
  var Ua = { isMounted: function(n) {
    return (n = n._reactInternals) ? qr(n) === n : !1;
  }, enqueueSetState: function(n, r, s) {
    n = n._reactInternals;
    var u = xt(), p = Or(n), g = Jn(u, p);
    g.payload = r, s != null && (g.callback = s), r = Sr(n, g, p), r !== null && (mn(r, n, p, u), Aa(r, n, p));
  }, enqueueReplaceState: function(n, r, s) {
    n = n._reactInternals;
    var u = xt(), p = Or(n), g = Jn(u, p);
    g.tag = 1, g.payload = r, s != null && (g.callback = s), r = Sr(n, g, p), r !== null && (mn(r, n, p, u), Aa(r, n, p));
  }, enqueueForceUpdate: function(n, r) {
    n = n._reactInternals;
    var s = xt(), u = Or(n), p = Jn(s, u);
    p.tag = 2, r != null && (p.callback = r), r = Sr(n, p, u), r !== null && (mn(r, n, u, s), Aa(r, n, u));
  } };
  function gm(n, r, s, u, p, g, O) {
    return n = n.stateNode, typeof n.shouldComponentUpdate == "function" ? n.shouldComponentUpdate(u, g, O) : r.prototype && r.prototype.isPureReactComponent ? !Ko(s, u) || !Ko(p, g) : !0;
  }
  function vm(n, r, s) {
    var u = !1, p = gr, g = r.contextType;
    return typeof g == "object" && g !== null ? g = Xt(g) : (p = Mt(r) ? Yr : Ct.current, u = r.contextTypes, g = (u = u != null) ? zi(n, p) : gr), r = new r(s, g), n.memoizedState = r.state !== null && r.state !== void 0 ? r.state : null, r.updater = Ua, n.stateNode = r, r._reactInternals = n, u && (n = n.stateNode, n.__reactInternalMemoizedUnmaskedChildContext = p, n.__reactInternalMemoizedMaskedChildContext = g), r;
  }
  function _m(n, r, s, u) {
    n = r.state, typeof r.componentWillReceiveProps == "function" && r.componentWillReceiveProps(s, u), typeof r.UNSAFE_componentWillReceiveProps == "function" && r.UNSAFE_componentWillReceiveProps(s, u), r.state !== n && Ua.enqueueReplaceState(r, r.state, null);
  }
  function gc(n, r, s, u) {
    var p = n.stateNode;
    p.props = s, p.state = n.memoizedState, p.refs = {}, rc(n);
    var g = r.contextType;
    typeof g == "object" && g !== null ? p.context = Xt(g) : (g = Mt(r) ? Yr : Ct.current, p.context = zi(n, g)), p.state = n.memoizedState, g = r.getDerivedStateFromProps, typeof g == "function" && (yc(n, r, g, s), p.state = n.memoizedState), typeof r.getDerivedStateFromProps == "function" || typeof p.getSnapshotBeforeUpdate == "function" || typeof p.UNSAFE_componentWillMount != "function" && typeof p.componentWillMount != "function" || (r = p.state, typeof p.componentWillMount == "function" && p.componentWillMount(), typeof p.UNSAFE_componentWillMount == "function" && p.UNSAFE_componentWillMount(), r !== p.state && Ua.enqueueReplaceState(p, p.state, null), xa(n, s, p, u), p.state = n.memoizedState), typeof p.componentDidMount == "function" && (n.flags |= 4194308);
  }
  function Yi(n, r) {
    try {
      var s = "", u = r;
      do
        s += I(u), u = u.return;
      while (u);
      var p = s;
    } catch (g) {
      p = `
Error generating stack: ` + g.message + `
` + g.stack;
    }
    return { value: n, source: r, stack: p, digest: null };
  }
  function vc(n, r, s) {
    return { value: n, source: null, stack: s ?? null, digest: r ?? null };
  }
  function _c(n, r) {
    try {
      console.error(r.value);
    } catch (s) {
      setTimeout(function() {
        throw s;
      });
    }
  }
  var Fw = typeof WeakMap == "function" ? WeakMap : Map;
  function Sm(n, r, s) {
    s = Jn(-1, s), s.tag = 3, s.payload = { element: null };
    var u = r.value;
    return s.callback = function() {
      qa || (qa = !0, bc = u), _c(n, r);
    }, s;
  }
  function wm(n, r, s) {
    s = Jn(-1, s), s.tag = 3;
    var u = n.type.getDerivedStateFromError;
    if (typeof u == "function") {
      var p = r.value;
      s.payload = function() {
        return u(p);
      }, s.callback = function() {
        _c(n, r);
      };
    }
    var g = n.stateNode;
    return g !== null && typeof g.componentDidCatch == "function" && (s.callback = function() {
      _c(n, r), typeof u != "function" && (Er === null ? Er = /* @__PURE__ */ new Set([this]) : Er.add(this));
      var O = r.stack;
      this.componentDidCatch(r.value, { componentStack: O !== null ? O : "" });
    }), s;
  }
  function Em(n, r, s) {
    var u = n.pingCache;
    if (u === null) {
      u = n.pingCache = new Fw();
      var p = /* @__PURE__ */ new Set();
      u.set(r, p);
    } else p = u.get(r), p === void 0 && (p = /* @__PURE__ */ new Set(), u.set(r, p));
    p.has(s) || (p.add(s), n = Yw.bind(null, n, r, s), r.then(n, n));
  }
  function $m(n) {
    do {
      var r;
      if ((r = n.tag === 13) && (r = n.memoizedState, r = r !== null ? r.dehydrated !== null : !0), r) return n;
      n = n.return;
    } while (n !== null);
    return null;
  }
  function Om(n, r, s, u, p) {
    return n.mode & 1 ? (n.flags |= 65536, n.lanes = p, n) : (n === r ? n.flags |= 65536 : (n.flags |= 128, s.flags |= 131072, s.flags &= -52805, s.tag === 1 && (s.alternate === null ? s.tag = 17 : (r = Jn(-1, 1), r.tag = 2, Sr(s, r, 1))), s.lanes |= 1), n);
  }
  var Rw = T.ReactCurrentOwner, Lt = !1;
  function At(n, r, s, u) {
    r.child = n === null ? Kh(r, null, s, u) : Wi(r, n.child, s, u);
  }
  function Pm(n, r, s, u, p) {
    s = s.render;
    var g = r.ref;
    return qi(r, p), u = cc(n, r, s, u, g, p), s = fc(), n !== null && !Lt ? (r.updateQueue = n.updateQueue, r.flags &= -2053, n.lanes &= ~p, Xn(n, r, p)) : (tt && s && qu(r), r.flags |= 1, At(n, r, u, p), r.child);
  }
  function Cm(n, r, s, u, p) {
    if (n === null) {
      var g = s.type;
      return typeof g == "function" && !zc(g) && g.defaultProps === void 0 && s.compare === null && s.defaultProps === void 0 ? (r.tag = 15, r.type = g, km(n, r, g, u, p)) : (n = Za(s.type, null, u, r, r.mode, p), n.ref = r.ref, n.return = r, r.child = n);
    }
    if (g = n.child, !(n.lanes & p)) {
      var O = g.memoizedProps;
      if (s = s.compare, s = s !== null ? s : Ko, s(O, u) && n.ref === r.ref) return Xn(n, r, p);
    }
    return r.flags |= 1, n = Cr(g, u), n.ref = r.ref, n.return = r, r.child = n;
  }
  function km(n, r, s, u, p) {
    if (n !== null) {
      var g = n.memoizedProps;
      if (Ko(g, u) && n.ref === r.ref) if (Lt = !1, r.pendingProps = u = g, (n.lanes & p) !== 0) n.flags & 131072 && (Lt = !0);
      else return r.lanes = n.lanes, Xn(n, r, p);
    }
    return Sc(n, r, s, u, p);
  }
  function Tm(n, r, s) {
    var u = r.pendingProps, p = u.children, g = n !== null ? n.memoizedState : null;
    if (u.mode === "hidden") if (!(r.mode & 1)) r.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, He(Ji, Yt), Yt |= s;
    else {
      if (!(s & 1073741824)) return n = g !== null ? g.baseLanes | s : s, r.lanes = r.childLanes = 1073741824, r.memoizedState = { baseLanes: n, cachePool: null, transitions: null }, r.updateQueue = null, He(Ji, Yt), Yt |= n, null;
      r.memoizedState = { baseLanes: 0, cachePool: null, transitions: null }, u = g !== null ? g.baseLanes : s, He(Ji, Yt), Yt |= u;
    }
    else g !== null ? (u = g.baseLanes | s, r.memoizedState = null) : u = s, He(Ji, Yt), Yt |= u;
    return At(n, r, p, s), r.child;
  }
  function Nm(n, r) {
    var s = r.ref;
    (n === null && s !== null || n !== null && n.ref !== s) && (r.flags |= 512, r.flags |= 2097152);
  }
  function Sc(n, r, s, u, p) {
    var g = Mt(s) ? Yr : Ct.current;
    return g = zi(r, g), qi(r, p), s = cc(n, r, s, u, g, p), u = fc(), n !== null && !Lt ? (r.updateQueue = n.updateQueue, r.flags &= -2053, n.lanes &= ~p, Xn(n, r, p)) : (tt && u && qu(r), r.flags |= 1, At(n, r, s, p), r.child);
  }
  function Im(n, r, s, u, p) {
    if (Mt(s)) {
      var g = !0;
      Oa(r);
    } else g = !1;
    if (qi(r, p), r.stateNode === null) Va(n, r), vm(r, s, u), gc(r, s, u, p), u = !0;
    else if (n === null) {
      var O = r.stateNode, A = r.memoizedProps;
      O.props = A;
      var M = O.context, Y = s.contextType;
      typeof Y == "object" && Y !== null ? Y = Xt(Y) : (Y = Mt(s) ? Yr : Ct.current, Y = zi(r, Y));
      var te = s.getDerivedStateFromProps, oe = typeof te == "function" || typeof O.getSnapshotBeforeUpdate == "function";
      oe || typeof O.UNSAFE_componentWillReceiveProps != "function" && typeof O.componentWillReceiveProps != "function" || (A !== u || M !== Y) && _m(r, O, u, Y), _r = !1;
      var ee = r.memoizedState;
      O.state = ee, xa(r, u, O, p), M = r.memoizedState, A !== u || ee !== M || Dt.current || _r ? (typeof te == "function" && (yc(r, s, te, u), M = r.memoizedState), (A = _r || gm(r, s, A, u, ee, M, Y)) ? (oe || typeof O.UNSAFE_componentWillMount != "function" && typeof O.componentWillMount != "function" || (typeof O.componentWillMount == "function" && O.componentWillMount(), typeof O.UNSAFE_componentWillMount == "function" && O.UNSAFE_componentWillMount()), typeof O.componentDidMount == "function" && (r.flags |= 4194308)) : (typeof O.componentDidMount == "function" && (r.flags |= 4194308), r.memoizedProps = u, r.memoizedState = M), O.props = u, O.state = M, O.context = Y, u = A) : (typeof O.componentDidMount == "function" && (r.flags |= 4194308), u = !1);
    } else {
      O = r.stateNode, Hh(n, r), A = r.memoizedProps, Y = r.type === r.elementType ? A : dn(r.type, A), O.props = Y, oe = r.pendingProps, ee = O.context, M = s.contextType, typeof M == "object" && M !== null ? M = Xt(M) : (M = Mt(s) ? Yr : Ct.current, M = zi(r, M));
      var de = s.getDerivedStateFromProps;
      (te = typeof de == "function" || typeof O.getSnapshotBeforeUpdate == "function") || typeof O.UNSAFE_componentWillReceiveProps != "function" && typeof O.componentWillReceiveProps != "function" || (A !== oe || ee !== M) && _m(r, O, u, M), _r = !1, ee = r.memoizedState, O.state = ee, xa(r, u, O, p);
      var ye = r.memoizedState;
      A !== oe || ee !== ye || Dt.current || _r ? (typeof de == "function" && (yc(r, s, de, u), ye = r.memoizedState), (Y = _r || gm(r, s, Y, u, ee, ye, M) || !1) ? (te || typeof O.UNSAFE_componentWillUpdate != "function" && typeof O.componentWillUpdate != "function" || (typeof O.componentWillUpdate == "function" && O.componentWillUpdate(u, ye, M), typeof O.UNSAFE_componentWillUpdate == "function" && O.UNSAFE_componentWillUpdate(u, ye, M)), typeof O.componentDidUpdate == "function" && (r.flags |= 4), typeof O.getSnapshotBeforeUpdate == "function" && (r.flags |= 1024)) : (typeof O.componentDidUpdate != "function" || A === n.memoizedProps && ee === n.memoizedState || (r.flags |= 4), typeof O.getSnapshotBeforeUpdate != "function" || A === n.memoizedProps && ee === n.memoizedState || (r.flags |= 1024), r.memoizedProps = u, r.memoizedState = ye), O.props = u, O.state = ye, O.context = M, u = Y) : (typeof O.componentDidUpdate != "function" || A === n.memoizedProps && ee === n.memoizedState || (r.flags |= 4), typeof O.getSnapshotBeforeUpdate != "function" || A === n.memoizedProps && ee === n.memoizedState || (r.flags |= 1024), u = !1);
    }
    return wc(n, r, s, u, g, p);
  }
  function wc(n, r, s, u, p, g) {
    Nm(n, r);
    var O = (r.flags & 128) !== 0;
    if (!u && !O) return p && Fh(r, s, !1), Xn(n, r, g);
    u = r.stateNode, Rw.current = r;
    var A = O && typeof s.getDerivedStateFromError != "function" ? null : u.render();
    return r.flags |= 1, n !== null && O ? (r.child = Wi(r, n.child, null, g), r.child = Wi(r, null, A, g)) : At(n, r, A, g), r.memoizedState = u.state, p && Fh(r, s, !0), r.child;
  }
  function jm(n) {
    var r = n.stateNode;
    r.pendingContext ? xh(n, r.pendingContext, r.pendingContext !== r.context) : r.context && xh(n, r.context, !1), ic(n, r.containerInfo);
  }
  function Am(n, r, s, u, p) {
    return Ki(), Ju(p), r.flags |= 256, At(n, r, s, u), r.child;
  }
  var Ec = { dehydrated: null, treeContext: null, retryLane: 0 };
  function $c(n) {
    return { baseLanes: n, cachePool: null, transitions: null };
  }
  function xm(n, r, s) {
    var u = r.pendingProps, p = rt.current, g = !1, O = (r.flags & 128) !== 0, A;
    if ((A = O) || (A = n !== null && n.memoizedState === null ? !1 : (p & 2) !== 0), A ? (g = !0, r.flags &= -129) : (n === null || n.memoizedState !== null) && (p |= 1), He(rt, p & 1), n === null)
      return Qu(r), n = r.memoizedState, n !== null && (n = n.dehydrated, n !== null) ? (r.mode & 1 ? n.data === "$!" ? r.lanes = 8 : r.lanes = 1073741824 : r.lanes = 1, null) : (O = u.children, n = u.fallback, g ? (u = r.mode, g = r.child, O = { mode: "hidden", children: O }, !(u & 1) && g !== null ? (g.childLanes = 0, g.pendingProps = O) : g = el(O, u, 0, null), n = oi(n, u, s, null), g.return = r, n.return = r, g.sibling = n, r.child = g, r.child.memoizedState = $c(s), r.memoizedState = Ec, n) : Oc(r, O));
    if (p = n.memoizedState, p !== null && (A = p.dehydrated, A !== null)) return Dw(n, r, O, u, A, p, s);
    if (g) {
      g = u.fallback, O = r.mode, p = n.child, A = p.sibling;
      var M = { mode: "hidden", children: u.children };
      return !(O & 1) && r.child !== p ? (u = r.child, u.childLanes = 0, u.pendingProps = M, r.deletions = null) : (u = Cr(p, M), u.subtreeFlags = p.subtreeFlags & 14680064), A !== null ? g = Cr(A, g) : (g = oi(g, O, s, null), g.flags |= 2), g.return = r, u.return = r, u.sibling = g, r.child = u, u = g, g = r.child, O = n.child.memoizedState, O = O === null ? $c(s) : { baseLanes: O.baseLanes | s, cachePool: null, transitions: O.transitions }, g.memoizedState = O, g.childLanes = n.childLanes & ~s, r.memoizedState = Ec, u;
    }
    return g = n.child, n = g.sibling, u = Cr(g, { mode: "visible", children: u.children }), !(r.mode & 1) && (u.lanes = s), u.return = r, u.sibling = null, n !== null && (s = r.deletions, s === null ? (r.deletions = [n], r.flags |= 16) : s.push(n)), r.child = u, r.memoizedState = null, u;
  }
  function Oc(n, r) {
    return r = el({ mode: "visible", children: r }, n.mode, 0, null), r.return = n, n.child = r;
  }
  function za(n, r, s, u) {
    return u !== null && Ju(u), Wi(r, n.child, null, s), n = Oc(r, r.pendingProps.children), n.flags |= 2, r.memoizedState = null, n;
  }
  function Dw(n, r, s, u, p, g, O) {
    if (s)
      return r.flags & 256 ? (r.flags &= -257, u = vc(Error(i(422))), za(n, r, O, u)) : r.memoizedState !== null ? (r.child = n.child, r.flags |= 128, null) : (g = u.fallback, p = r.mode, u = el({ mode: "visible", children: u.children }, p, 0, null), g = oi(g, p, O, null), g.flags |= 2, u.return = r, g.return = r, u.sibling = g, r.child = u, r.mode & 1 && Wi(r, n.child, null, O), r.child.memoizedState = $c(O), r.memoizedState = Ec, g);
    if (!(r.mode & 1)) return za(n, r, O, null);
    if (p.data === "$!") {
      if (u = p.nextSibling && p.nextSibling.dataset, u) var A = u.dgst;
      return u = A, g = Error(i(419)), u = vc(g, u, void 0), za(n, r, O, u);
    }
    if (A = (O & n.childLanes) !== 0, Lt || A) {
      if (u = vt, u !== null) {
        switch (O & -O) {
          case 4:
            p = 2;
            break;
          case 16:
            p = 8;
            break;
          case 64:
          case 128:
          case 256:
          case 512:
          case 1024:
          case 2048:
          case 4096:
          case 8192:
          case 16384:
          case 32768:
          case 65536:
          case 131072:
          case 262144:
          case 524288:
          case 1048576:
          case 2097152:
          case 4194304:
          case 8388608:
          case 16777216:
          case 33554432:
          case 67108864:
            p = 32;
            break;
          case 536870912:
            p = 268435456;
            break;
          default:
            p = 0;
        }
        p = p & (u.suspendedLanes | O) ? 0 : p, p !== 0 && p !== g.retryLane && (g.retryLane = p, Qn(n, p), mn(u, n, p, -1));
      }
      return Uc(), u = vc(Error(i(421))), za(n, r, O, u);
    }
    return p.data === "$?" ? (r.flags |= 128, r.child = n.child, r = Qw.bind(null, n), p._reactRetry = r, null) : (n = g.treeContext, Gt = mr(p.nextSibling), qt = r, tt = !0, fn = null, n !== null && (Qt[Jt++] = Gn, Qt[Jt++] = Yn, Qt[Jt++] = Qr, Gn = n.id, Yn = n.overflow, Qr = r), r = Oc(r, u.children), r.flags |= 4096, r);
  }
  function bm(n, r, s) {
    n.lanes |= r;
    var u = n.alternate;
    u !== null && (u.lanes |= r), tc(n.return, r, s);
  }
  function Pc(n, r, s, u, p) {
    var g = n.memoizedState;
    g === null ? n.memoizedState = { isBackwards: r, rendering: null, renderingStartTime: 0, last: u, tail: s, tailMode: p } : (g.isBackwards = r, g.rendering = null, g.renderingStartTime = 0, g.last = u, g.tail = s, g.tailMode = p);
  }
  function Fm(n, r, s) {
    var u = r.pendingProps, p = u.revealOrder, g = u.tail;
    if (At(n, r, u.children, s), u = rt.current, u & 2) u = u & 1 | 2, r.flags |= 128;
    else {
      if (n !== null && n.flags & 128) e: for (n = r.child; n !== null; ) {
        if (n.tag === 13) n.memoizedState !== null && bm(n, s, r);
        else if (n.tag === 19) bm(n, s, r);
        else if (n.child !== null) {
          n.child.return = n, n = n.child;
          continue;
        }
        if (n === r) break e;
        for (; n.sibling === null; ) {
          if (n.return === null || n.return === r) break e;
          n = n.return;
        }
        n.sibling.return = n.return, n = n.sibling;
      }
      u &= 1;
    }
    if (He(rt, u), !(r.mode & 1)) r.memoizedState = null;
    else switch (p) {
      case "forwards":
        for (s = r.child, p = null; s !== null; ) n = s.alternate, n !== null && ba(n) === null && (p = s), s = s.sibling;
        s = p, s === null ? (p = r.child, r.child = null) : (p = s.sibling, s.sibling = null), Pc(r, !1, p, s, g);
        break;
      case "backwards":
        for (s = null, p = r.child, r.child = null; p !== null; ) {
          if (n = p.alternate, n !== null && ba(n) === null) {
            r.child = p;
            break;
          }
          n = p.sibling, p.sibling = s, s = p, p = n;
        }
        Pc(r, !0, s, null, g);
        break;
      case "together":
        Pc(r, !1, null, null, void 0);
        break;
      default:
        r.memoizedState = null;
    }
    return r.child;
  }
  function Va(n, r) {
    !(r.mode & 1) && n !== null && (n.alternate = null, r.alternate = null, r.flags |= 2);
  }
  function Xn(n, r, s) {
    if (n !== null && (r.dependencies = n.dependencies), ti |= r.lanes, !(s & r.childLanes)) return null;
    if (n !== null && r.child !== n.child) throw Error(i(153));
    if (r.child !== null) {
      for (n = r.child, s = Cr(n, n.pendingProps), r.child = s, s.return = r; n.sibling !== null; ) n = n.sibling, s = s.sibling = Cr(n, n.pendingProps), s.return = r;
      s.sibling = null;
    }
    return r.child;
  }
  function Mw(n, r, s) {
    switch (r.tag) {
      case 3:
        jm(r), Ki();
        break;
      case 5:
        Yh(r);
        break;
      case 1:
        Mt(r.type) && Oa(r);
        break;
      case 4:
        ic(r, r.stateNode.containerInfo);
        break;
      case 10:
        var u = r.type._context, p = r.memoizedProps.value;
        He(Ia, u._currentValue), u._currentValue = p;
        break;
      case 13:
        if (u = r.memoizedState, u !== null)
          return u.dehydrated !== null ? (He(rt, rt.current & 1), r.flags |= 128, null) : s & r.child.childLanes ? xm(n, r, s) : (He(rt, rt.current & 1), n = Xn(n, r, s), n !== null ? n.sibling : null);
        He(rt, rt.current & 1);
        break;
      case 19:
        if (u = (s & r.childLanes) !== 0, n.flags & 128) {
          if (u) return Fm(n, r, s);
          r.flags |= 128;
        }
        if (p = r.memoizedState, p !== null && (p.rendering = null, p.tail = null, p.lastEffect = null), He(rt, rt.current), u) break;
        return null;
      case 22:
      case 23:
        return r.lanes = 0, Tm(n, r, s);
    }
    return Xn(n, r, s);
  }
  var Rm, Cc, Dm, Mm;
  Rm = function(n, r) {
    for (var s = r.child; s !== null; ) {
      if (s.tag === 5 || s.tag === 6) n.appendChild(s.stateNode);
      else if (s.tag !== 4 && s.child !== null) {
        s.child.return = s, s = s.child;
        continue;
      }
      if (s === r) break;
      for (; s.sibling === null; ) {
        if (s.return === null || s.return === r) return;
        s = s.return;
      }
      s.sibling.return = s.return, s = s.sibling;
    }
  }, Cc = function() {
  }, Dm = function(n, r, s, u) {
    var p = n.memoizedProps;
    if (p !== u) {
      n = r.stateNode, Zr(kn.current);
      var g = null;
      switch (s) {
        case "input":
          p = ze(n, p), u = ze(n, u), g = [];
          break;
        case "select":
          p = z({}, p, { value: void 0 }), u = z({}, u, { value: void 0 }), g = [];
          break;
        case "textarea":
          p = Br(n, p), u = Br(n, u), g = [];
          break;
        default:
          typeof p.onClick != "function" && typeof u.onClick == "function" && (n.onclick = wa);
      }
      su(s, u);
      var O;
      s = null;
      for (Y in p) if (!u.hasOwnProperty(Y) && p.hasOwnProperty(Y) && p[Y] != null) if (Y === "style") {
        var A = p[Y];
        for (O in A) A.hasOwnProperty(O) && (s || (s = {}), s[O] = "");
      } else Y !== "dangerouslySetInnerHTML" && Y !== "children" && Y !== "suppressContentEditableWarning" && Y !== "suppressHydrationWarning" && Y !== "autoFocus" && (a.hasOwnProperty(Y) ? g || (g = []) : (g = g || []).push(Y, null));
      for (Y in u) {
        var M = u[Y];
        if (A = p != null ? p[Y] : void 0, u.hasOwnProperty(Y) && M !== A && (M != null || A != null)) if (Y === "style") if (A) {
          for (O in A) !A.hasOwnProperty(O) || M && M.hasOwnProperty(O) || (s || (s = {}), s[O] = "");
          for (O in M) M.hasOwnProperty(O) && A[O] !== M[O] && (s || (s = {}), s[O] = M[O]);
        } else s || (g || (g = []), g.push(
          Y,
          s
        )), s = M;
        else Y === "dangerouslySetInnerHTML" ? (M = M ? M.__html : void 0, A = A ? A.__html : void 0, M != null && A !== M && (g = g || []).push(Y, M)) : Y === "children" ? typeof M != "string" && typeof M != "number" || (g = g || []).push(Y, "" + M) : Y !== "suppressContentEditableWarning" && Y !== "suppressHydrationWarning" && (a.hasOwnProperty(Y) ? (M != null && Y === "onScroll" && Ye("scroll", n), g || A === M || (g = [])) : (g = g || []).push(Y, M));
      }
      s && (g = g || []).push("style", s);
      var Y = g;
      (r.updateQueue = Y) && (r.flags |= 4);
    }
  }, Mm = function(n, r, s, u) {
    s !== u && (r.flags |= 4);
  };
  function os(n, r) {
    if (!tt) switch (n.tailMode) {
      case "hidden":
        r = n.tail;
        for (var s = null; r !== null; ) r.alternate !== null && (s = r), r = r.sibling;
        s === null ? n.tail = null : s.sibling = null;
        break;
      case "collapsed":
        s = n.tail;
        for (var u = null; s !== null; ) s.alternate !== null && (u = s), s = s.sibling;
        u === null ? r || n.tail === null ? n.tail = null : n.tail.sibling = null : u.sibling = null;
    }
  }
  function Tt(n) {
    var r = n.alternate !== null && n.alternate.child === n.child, s = 0, u = 0;
    if (r) for (var p = n.child; p !== null; ) s |= p.lanes | p.childLanes, u |= p.subtreeFlags & 14680064, u |= p.flags & 14680064, p.return = n, p = p.sibling;
    else for (p = n.child; p !== null; ) s |= p.lanes | p.childLanes, u |= p.subtreeFlags, u |= p.flags, p.return = n, p = p.sibling;
    return n.subtreeFlags |= u, n.childLanes = s, r;
  }
  function Lw(n, r, s) {
    var u = r.pendingProps;
    switch (Gu(r), r.tag) {
      case 2:
      case 16:
      case 15:
      case 0:
      case 11:
      case 7:
      case 8:
      case 12:
      case 9:
      case 14:
        return Tt(r), null;
      case 1:
        return Mt(r.type) && $a(), Tt(r), null;
      case 3:
        return u = r.stateNode, Gi(), Qe(Dt), Qe(Ct), ac(), u.pendingContext && (u.context = u.pendingContext, u.pendingContext = null), (n === null || n.child === null) && (Ta(r) ? r.flags |= 4 : n === null || n.memoizedState.isDehydrated && !(r.flags & 256) || (r.flags |= 1024, fn !== null && (Dc(fn), fn = null))), Cc(n, r), Tt(r), null;
      case 5:
        oc(r);
        var p = Zr(es.current);
        if (s = r.type, n !== null && r.stateNode != null) Dm(n, r, s, u, p), n.ref !== r.ref && (r.flags |= 512, r.flags |= 2097152);
        else {
          if (!u) {
            if (r.stateNode === null) throw Error(i(166));
            return Tt(r), null;
          }
          if (n = Zr(kn.current), Ta(r)) {
            u = r.stateNode, s = r.type;
            var g = r.memoizedProps;
            switch (u[Cn] = r, u[Yo] = g, n = (r.mode & 1) !== 0, s) {
              case "dialog":
                Ye("cancel", u), Ye("close", u);
                break;
              case "iframe":
              case "object":
              case "embed":
                Ye("load", u);
                break;
              case "video":
              case "audio":
                for (p = 0; p < Ho.length; p++) Ye(Ho[p], u);
                break;
              case "source":
                Ye("error", u);
                break;
              case "img":
              case "image":
              case "link":
                Ye(
                  "error",
                  u
                ), Ye("load", u);
                break;
              case "details":
                Ye("toggle", u);
                break;
              case "input":
                Rt(u, g), Ye("invalid", u);
                break;
              case "select":
                u._wrapperState = { wasMultiple: !!g.multiple }, Ye("invalid", u);
                break;
              case "textarea":
                ki(u, g), Ye("invalid", u);
            }
            su(s, g), p = null;
            for (var O in g) if (g.hasOwnProperty(O)) {
              var A = g[O];
              O === "children" ? typeof A == "string" ? u.textContent !== A && (g.suppressHydrationWarning !== !0 && Sa(u.textContent, A, n), p = ["children", A]) : typeof A == "number" && u.textContent !== "" + A && (g.suppressHydrationWarning !== !0 && Sa(
                u.textContent,
                A,
                n
              ), p = ["children", "" + A]) : a.hasOwnProperty(O) && A != null && O === "onScroll" && Ye("scroll", u);
            }
            switch (s) {
              case "input":
                $e(u), Pt(u, g, !0);
                break;
              case "textarea":
                $e(u), Ni(u);
                break;
              case "select":
              case "option":
                break;
              default:
                typeof g.onClick == "function" && (u.onclick = wa);
            }
            u = p, r.updateQueue = u, u !== null && (r.flags |= 4);
          } else {
            O = p.nodeType === 9 ? p : p.ownerDocument, n === "http://www.w3.org/1999/xhtml" && (n = lr(s)), n === "http://www.w3.org/1999/xhtml" ? s === "script" ? (n = O.createElement("div"), n.innerHTML = "<script><\/script>", n = n.removeChild(n.firstChild)) : typeof u.is == "string" ? n = O.createElement(s, { is: u.is }) : (n = O.createElement(s), s === "select" && (O = n, u.multiple ? O.multiple = !0 : u.size && (O.size = u.size))) : n = O.createElementNS(n, s), n[Cn] = r, n[Yo] = u, Rm(n, r, !1, !1), r.stateNode = n;
            e: {
              switch (O = au(s, u), s) {
                case "dialog":
                  Ye("cancel", n), Ye("close", n), p = u;
                  break;
                case "iframe":
                case "object":
                case "embed":
                  Ye("load", n), p = u;
                  break;
                case "video":
                case "audio":
                  for (p = 0; p < Ho.length; p++) Ye(Ho[p], n);
                  p = u;
                  break;
                case "source":
                  Ye("error", n), p = u;
                  break;
                case "img":
                case "image":
                case "link":
                  Ye(
                    "error",
                    n
                  ), Ye("load", n), p = u;
                  break;
                case "details":
                  Ye("toggle", n), p = u;
                  break;
                case "input":
                  Rt(n, u), p = ze(n, u), Ye("invalid", n);
                  break;
                case "option":
                  p = u;
                  break;
                case "select":
                  n._wrapperState = { wasMultiple: !!u.multiple }, p = z({}, u, { value: void 0 }), Ye("invalid", n);
                  break;
                case "textarea":
                  ki(n, u), p = Br(n, u), Ye("invalid", n);
                  break;
                default:
                  p = u;
              }
              su(s, p), A = p;
              for (g in A) if (A.hasOwnProperty(g)) {
                var M = A[g];
                g === "style" ? kp(n, M) : g === "dangerouslySetInnerHTML" ? (M = M ? M.__html : void 0, M != null && ko(n, M)) : g === "children" ? typeof M == "string" ? (s !== "textarea" || M !== "") && Hr(n, M) : typeof M == "number" && Hr(n, "" + M) : g !== "suppressContentEditableWarning" && g !== "suppressHydrationWarning" && g !== "autoFocus" && (a.hasOwnProperty(g) ? M != null && g === "onScroll" && Ye("scroll", n) : M != null && j(n, g, M, O));
              }
              switch (s) {
                case "input":
                  $e(n), Pt(n, u, !1);
                  break;
                case "textarea":
                  $e(n), Ni(n);
                  break;
                case "option":
                  u.value != null && n.setAttribute("value", "" + J(u.value));
                  break;
                case "select":
                  n.multiple = !!u.multiple, g = u.value, g != null ? On(n, !!u.multiple, g, !1) : u.defaultValue != null && On(
                    n,
                    !!u.multiple,
                    u.defaultValue,
                    !0
                  );
                  break;
                default:
                  typeof p.onClick == "function" && (n.onclick = wa);
              }
              switch (s) {
                case "button":
                case "input":
                case "select":
                case "textarea":
                  u = !!u.autoFocus;
                  break e;
                case "img":
                  u = !0;
                  break e;
                default:
                  u = !1;
              }
            }
            u && (r.flags |= 4);
          }
          r.ref !== null && (r.flags |= 512, r.flags |= 2097152);
        }
        return Tt(r), null;
      case 6:
        if (n && r.stateNode != null) Mm(n, r, n.memoizedProps, u);
        else {
          if (typeof u != "string" && r.stateNode === null) throw Error(i(166));
          if (s = Zr(es.current), Zr(kn.current), Ta(r)) {
            if (u = r.stateNode, s = r.memoizedProps, u[Cn] = r, (g = u.nodeValue !== s) && (n = qt, n !== null)) switch (n.tag) {
              case 3:
                Sa(u.nodeValue, s, (n.mode & 1) !== 0);
                break;
              case 5:
                n.memoizedProps.suppressHydrationWarning !== !0 && Sa(u.nodeValue, s, (n.mode & 1) !== 0);
            }
            g && (r.flags |= 4);
          } else u = (s.nodeType === 9 ? s : s.ownerDocument).createTextNode(u), u[Cn] = r, r.stateNode = u;
        }
        return Tt(r), null;
      case 13:
        if (Qe(rt), u = r.memoizedState, n === null || n.memoizedState !== null && n.memoizedState.dehydrated !== null) {
          if (tt && Gt !== null && r.mode & 1 && !(r.flags & 128)) zh(), Ki(), r.flags |= 98560, g = !1;
          else if (g = Ta(r), u !== null && u.dehydrated !== null) {
            if (n === null) {
              if (!g) throw Error(i(318));
              if (g = r.memoizedState, g = g !== null ? g.dehydrated : null, !g) throw Error(i(317));
              g[Cn] = r;
            } else Ki(), !(r.flags & 128) && (r.memoizedState = null), r.flags |= 4;
            Tt(r), g = !1;
          } else fn !== null && (Dc(fn), fn = null), g = !0;
          if (!g) return r.flags & 65536 ? r : null;
        }
        return r.flags & 128 ? (r.lanes = s, r) : (u = u !== null, u !== (n !== null && n.memoizedState !== null) && u && (r.child.flags |= 8192, r.mode & 1 && (n === null || rt.current & 1 ? ht === 0 && (ht = 3) : Uc())), r.updateQueue !== null && (r.flags |= 4), Tt(r), null);
      case 4:
        return Gi(), Cc(n, r), n === null && qo(r.stateNode.containerInfo), Tt(r), null;
      case 10:
        return ec(r.type._context), Tt(r), null;
      case 17:
        return Mt(r.type) && $a(), Tt(r), null;
      case 19:
        if (Qe(rt), g = r.memoizedState, g === null) return Tt(r), null;
        if (u = (r.flags & 128) !== 0, O = g.rendering, O === null) if (u) os(g, !1);
        else {
          if (ht !== 0 || n !== null && n.flags & 128) for (n = r.child; n !== null; ) {
            if (O = ba(n), O !== null) {
              for (r.flags |= 128, os(g, !1), u = O.updateQueue, u !== null && (r.updateQueue = u, r.flags |= 4), r.subtreeFlags = 0, u = s, s = r.child; s !== null; ) g = s, n = u, g.flags &= 14680066, O = g.alternate, O === null ? (g.childLanes = 0, g.lanes = n, g.child = null, g.subtreeFlags = 0, g.memoizedProps = null, g.memoizedState = null, g.updateQueue = null, g.dependencies = null, g.stateNode = null) : (g.childLanes = O.childLanes, g.lanes = O.lanes, g.child = O.child, g.subtreeFlags = 0, g.deletions = null, g.memoizedProps = O.memoizedProps, g.memoizedState = O.memoizedState, g.updateQueue = O.updateQueue, g.type = O.type, n = O.dependencies, g.dependencies = n === null ? null : { lanes: n.lanes, firstContext: n.firstContext }), s = s.sibling;
              return He(rt, rt.current & 1 | 2), r.child;
            }
            n = n.sibling;
          }
          g.tail !== null && at() > Xi && (r.flags |= 128, u = !0, os(g, !1), r.lanes = 4194304);
        }
        else {
          if (!u) if (n = ba(O), n !== null) {
            if (r.flags |= 128, u = !0, s = n.updateQueue, s !== null && (r.updateQueue = s, r.flags |= 4), os(g, !0), g.tail === null && g.tailMode === "hidden" && !O.alternate && !tt) return Tt(r), null;
          } else 2 * at() - g.renderingStartTime > Xi && s !== 1073741824 && (r.flags |= 128, u = !0, os(g, !1), r.lanes = 4194304);
          g.isBackwards ? (O.sibling = r.child, r.child = O) : (s = g.last, s !== null ? s.sibling = O : r.child = O, g.last = O);
        }
        return g.tail !== null ? (r = g.tail, g.rendering = r, g.tail = r.sibling, g.renderingStartTime = at(), r.sibling = null, s = rt.current, He(rt, u ? s & 1 | 2 : s & 1), r) : (Tt(r), null);
      case 22:
      case 23:
        return Lc(), u = r.memoizedState !== null, n !== null && n.memoizedState !== null !== u && (r.flags |= 8192), u && r.mode & 1 ? Yt & 1073741824 && (Tt(r), r.subtreeFlags & 6 && (r.flags |= 8192)) : Tt(r), null;
      case 24:
        return null;
      case 25:
        return null;
    }
    throw Error(i(156, r.tag));
  }
  function Uw(n, r) {
    switch (Gu(r), r.tag) {
      case 1:
        return Mt(r.type) && $a(), n = r.flags, n & 65536 ? (r.flags = n & -65537 | 128, r) : null;
      case 3:
        return Gi(), Qe(Dt), Qe(Ct), ac(), n = r.flags, n & 65536 && !(n & 128) ? (r.flags = n & -65537 | 128, r) : null;
      case 5:
        return oc(r), null;
      case 13:
        if (Qe(rt), n = r.memoizedState, n !== null && n.dehydrated !== null) {
          if (r.alternate === null) throw Error(i(340));
          Ki();
        }
        return n = r.flags, n & 65536 ? (r.flags = n & -65537 | 128, r) : null;
      case 19:
        return Qe(rt), null;
      case 4:
        return Gi(), null;
      case 10:
        return ec(r.type._context), null;
      case 22:
      case 23:
        return Lc(), null;
      case 24:
        return null;
      default:
        return null;
    }
  }
  var Ba = !1, Nt = !1, zw = typeof WeakSet == "function" ? WeakSet : Set, me = null;
  function Qi(n, r) {
    var s = n.ref;
    if (s !== null) if (typeof s == "function") try {
      s(null);
    } catch (u) {
      st(n, r, u);
    }
    else s.current = null;
  }
  function kc(n, r, s) {
    try {
      s();
    } catch (u) {
      st(n, r, u);
    }
  }
  var Lm = !1;
  function Vw(n, r) {
    if (Lu = ua, n = gh(), ju(n)) {
      if ("selectionStart" in n) var s = { start: n.selectionStart, end: n.selectionEnd };
      else e: {
        s = (s = n.ownerDocument) && s.defaultView || window;
        var u = s.getSelection && s.getSelection();
        if (u && u.rangeCount !== 0) {
          s = u.anchorNode;
          var p = u.anchorOffset, g = u.focusNode;
          u = u.focusOffset;
          try {
            s.nodeType, g.nodeType;
          } catch {
            s = null;
            break e;
          }
          var O = 0, A = -1, M = -1, Y = 0, te = 0, oe = n, ee = null;
          t: for (; ; ) {
            for (var de; oe !== s || p !== 0 && oe.nodeType !== 3 || (A = O + p), oe !== g || u !== 0 && oe.nodeType !== 3 || (M = O + u), oe.nodeType === 3 && (O += oe.nodeValue.length), (de = oe.firstChild) !== null; )
              ee = oe, oe = de;
            for (; ; ) {
              if (oe === n) break t;
              if (ee === s && ++Y === p && (A = O), ee === g && ++te === u && (M = O), (de = oe.nextSibling) !== null) break;
              oe = ee, ee = oe.parentNode;
            }
            oe = de;
          }
          s = A === -1 || M === -1 ? null : { start: A, end: M };
        } else s = null;
      }
      s = s || { start: 0, end: 0 };
    } else s = null;
    for (Uu = { focusedElem: n, selectionRange: s }, ua = !1, me = r; me !== null; ) if (r = me, n = r.child, (r.subtreeFlags & 1028) !== 0 && n !== null) n.return = r, me = n;
    else for (; me !== null; ) {
      r = me;
      try {
        var ye = r.alternate;
        if (r.flags & 1024) switch (r.tag) {
          case 0:
          case 11:
          case 15:
            break;
          case 1:
            if (ye !== null) {
              var ge = ye.memoizedProps, lt = ye.memoizedState, K = r.stateNode, L = K.getSnapshotBeforeUpdate(r.elementType === r.type ? ge : dn(r.type, ge), lt);
              K.__reactInternalSnapshotBeforeUpdate = L;
            }
            break;
          case 3:
            var W = r.stateNode.containerInfo;
            W.nodeType === 1 ? W.textContent = "" : W.nodeType === 9 && W.documentElement && W.removeChild(W.documentElement);
            break;
          case 5:
          case 6:
          case 4:
          case 17:
            break;
          default:
            throw Error(i(163));
        }
      } catch (ue) {
        st(r, r.return, ue);
      }
      if (n = r.sibling, n !== null) {
        n.return = r.return, me = n;
        break;
      }
      me = r.return;
    }
    return ye = Lm, Lm = !1, ye;
  }
  function ss(n, r, s) {
    var u = r.updateQueue;
    if (u = u !== null ? u.lastEffect : null, u !== null) {
      var p = u = u.next;
      do {
        if ((p.tag & n) === n) {
          var g = p.destroy;
          p.destroy = void 0, g !== void 0 && kc(r, s, g);
        }
        p = p.next;
      } while (p !== u);
    }
  }
  function Ka(n, r) {
    if (r = r.updateQueue, r = r !== null ? r.lastEffect : null, r !== null) {
      var s = r = r.next;
      do {
        if ((s.tag & n) === n) {
          var u = s.create;
          s.destroy = u();
        }
        s = s.next;
      } while (s !== r);
    }
  }
  function Tc(n) {
    var r = n.ref;
    if (r !== null) {
      var s = n.stateNode;
      switch (n.tag) {
        case 5:
          n = s;
          break;
        default:
          n = s;
      }
      typeof r == "function" ? r(n) : r.current = n;
    }
  }
  function Um(n) {
    var r = n.alternate;
    r !== null && (n.alternate = null, Um(r)), n.child = null, n.deletions = null, n.sibling = null, n.tag === 5 && (r = n.stateNode, r !== null && (delete r[Cn], delete r[Yo], delete r[Ku], delete r[Ow], delete r[Pw])), n.stateNode = null, n.return = null, n.dependencies = null, n.memoizedProps = null, n.memoizedState = null, n.pendingProps = null, n.stateNode = null, n.updateQueue = null;
  }
  function zm(n) {
    return n.tag === 5 || n.tag === 3 || n.tag === 4;
  }
  function Vm(n) {
    e: for (; ; ) {
      for (; n.sibling === null; ) {
        if (n.return === null || zm(n.return)) return null;
        n = n.return;
      }
      for (n.sibling.return = n.return, n = n.sibling; n.tag !== 5 && n.tag !== 6 && n.tag !== 18; ) {
        if (n.flags & 2 || n.child === null || n.tag === 4) continue e;
        n.child.return = n, n = n.child;
      }
      if (!(n.flags & 2)) return n.stateNode;
    }
  }
  function Nc(n, r, s) {
    var u = n.tag;
    if (u === 5 || u === 6) n = n.stateNode, r ? s.nodeType === 8 ? s.parentNode.insertBefore(n, r) : s.insertBefore(n, r) : (s.nodeType === 8 ? (r = s.parentNode, r.insertBefore(n, s)) : (r = s, r.appendChild(n)), s = s._reactRootContainer, s != null || r.onclick !== null || (r.onclick = wa));
    else if (u !== 4 && (n = n.child, n !== null)) for (Nc(n, r, s), n = n.sibling; n !== null; ) Nc(n, r, s), n = n.sibling;
  }
  function Ic(n, r, s) {
    var u = n.tag;
    if (u === 5 || u === 6) n = n.stateNode, r ? s.insertBefore(n, r) : s.appendChild(n);
    else if (u !== 4 && (n = n.child, n !== null)) for (Ic(n, r, s), n = n.sibling; n !== null; ) Ic(n, r, s), n = n.sibling;
  }
  var St = null, pn = !1;
  function wr(n, r, s) {
    for (s = s.child; s !== null; ) Bm(n, r, s), s = s.sibling;
  }
  function Bm(n, r, s) {
    if (Pn && typeof Pn.onCommitFiberUnmount == "function") try {
      Pn.onCommitFiberUnmount(ra, s);
    } catch {
    }
    switch (s.tag) {
      case 5:
        Nt || Qi(s, r);
      case 6:
        var u = St, p = pn;
        St = null, wr(n, r, s), St = u, pn = p, St !== null && (pn ? (n = St, s = s.stateNode, n.nodeType === 8 ? n.parentNode.removeChild(s) : n.removeChild(s)) : St.removeChild(s.stateNode));
        break;
      case 18:
        St !== null && (pn ? (n = St, s = s.stateNode, n.nodeType === 8 ? Bu(n.parentNode, s) : n.nodeType === 1 && Bu(n, s), Mo(n)) : Bu(St, s.stateNode));
        break;
      case 4:
        u = St, p = pn, St = s.stateNode.containerInfo, pn = !0, wr(n, r, s), St = u, pn = p;
        break;
      case 0:
      case 11:
      case 14:
      case 15:
        if (!Nt && (u = s.updateQueue, u !== null && (u = u.lastEffect, u !== null))) {
          p = u = u.next;
          do {
            var g = p, O = g.destroy;
            g = g.tag, O !== void 0 && (g & 2 || g & 4) && kc(s, r, O), p = p.next;
          } while (p !== u);
        }
        wr(n, r, s);
        break;
      case 1:
        if (!Nt && (Qi(s, r), u = s.stateNode, typeof u.componentWillUnmount == "function")) try {
          u.props = s.memoizedProps, u.state = s.memoizedState, u.componentWillUnmount();
        } catch (A) {
          st(s, r, A);
        }
        wr(n, r, s);
        break;
      case 21:
        wr(n, r, s);
        break;
      case 22:
        s.mode & 1 ? (Nt = (u = Nt) || s.memoizedState !== null, wr(n, r, s), Nt = u) : wr(n, r, s);
        break;
      default:
        wr(n, r, s);
    }
  }
  function Km(n) {
    var r = n.updateQueue;
    if (r !== null) {
      n.updateQueue = null;
      var s = n.stateNode;
      s === null && (s = n.stateNode = new zw()), r.forEach(function(u) {
        var p = Jw.bind(null, n, u);
        s.has(u) || (s.add(u), u.then(p, p));
      });
    }
  }
  function hn(n, r) {
    var s = r.deletions;
    if (s !== null) for (var u = 0; u < s.length; u++) {
      var p = s[u];
      try {
        var g = n, O = r, A = O;
        e: for (; A !== null; ) {
          switch (A.tag) {
            case 5:
              St = A.stateNode, pn = !1;
              break e;
            case 3:
              St = A.stateNode.containerInfo, pn = !0;
              break e;
            case 4:
              St = A.stateNode.containerInfo, pn = !0;
              break e;
          }
          A = A.return;
        }
        if (St === null) throw Error(i(160));
        Bm(g, O, p), St = null, pn = !1;
        var M = p.alternate;
        M !== null && (M.return = null), p.return = null;
      } catch (Y) {
        st(p, r, Y);
      }
    }
    if (r.subtreeFlags & 12854) for (r = r.child; r !== null; ) Wm(r, n), r = r.sibling;
  }
  function Wm(n, r) {
    var s = n.alternate, u = n.flags;
    switch (n.tag) {
      case 0:
      case 11:
      case 14:
      case 15:
        if (hn(r, n), Nn(n), u & 4) {
          try {
            ss(3, n, n.return), Ka(3, n);
          } catch (ge) {
            st(n, n.return, ge);
          }
          try {
            ss(5, n, n.return);
          } catch (ge) {
            st(n, n.return, ge);
          }
        }
        break;
      case 1:
        hn(r, n), Nn(n), u & 512 && s !== null && Qi(s, s.return);
        break;
      case 5:
        if (hn(r, n), Nn(n), u & 512 && s !== null && Qi(s, s.return), n.flags & 32) {
          var p = n.stateNode;
          try {
            Hr(p, "");
          } catch (ge) {
            st(n, n.return, ge);
          }
        }
        if (u & 4 && (p = n.stateNode, p != null)) {
          var g = n.memoizedProps, O = s !== null ? s.memoizedProps : g, A = n.type, M = n.updateQueue;
          if (n.updateQueue = null, M !== null) try {
            A === "input" && g.type === "radio" && g.name != null && et(p, g), au(A, O);
            var Y = au(A, g);
            for (O = 0; O < M.length; O += 2) {
              var te = M[O], oe = M[O + 1];
              te === "style" ? kp(p, oe) : te === "dangerouslySetInnerHTML" ? ko(p, oe) : te === "children" ? Hr(p, oe) : j(p, te, oe, Y);
            }
            switch (A) {
              case "input":
                Wt(p, g);
                break;
              case "textarea":
                Ti(p, g);
                break;
              case "select":
                var ee = p._wrapperState.wasMultiple;
                p._wrapperState.wasMultiple = !!g.multiple;
                var de = g.value;
                de != null ? On(p, !!g.multiple, de, !1) : ee !== !!g.multiple && (g.defaultValue != null ? On(
                  p,
                  !!g.multiple,
                  g.defaultValue,
                  !0
                ) : On(p, !!g.multiple, g.multiple ? [] : "", !1));
            }
            p[Yo] = g;
          } catch (ge) {
            st(n, n.return, ge);
          }
        }
        break;
      case 6:
        if (hn(r, n), Nn(n), u & 4) {
          if (n.stateNode === null) throw Error(i(162));
          p = n.stateNode, g = n.memoizedProps;
          try {
            p.nodeValue = g;
          } catch (ge) {
            st(n, n.return, ge);
          }
        }
        break;
      case 3:
        if (hn(r, n), Nn(n), u & 4 && s !== null && s.memoizedState.isDehydrated) try {
          Mo(r.containerInfo);
        } catch (ge) {
          st(n, n.return, ge);
        }
        break;
      case 4:
        hn(r, n), Nn(n);
        break;
      case 13:
        hn(r, n), Nn(n), p = n.child, p.flags & 8192 && (g = p.memoizedState !== null, p.stateNode.isHidden = g, !g || p.alternate !== null && p.alternate.memoizedState !== null || (xc = at())), u & 4 && Km(n);
        break;
      case 22:
        if (te = s !== null && s.memoizedState !== null, n.mode & 1 ? (Nt = (Y = Nt) || te, hn(r, n), Nt = Y) : hn(r, n), Nn(n), u & 8192) {
          if (Y = n.memoizedState !== null, (n.stateNode.isHidden = Y) && !te && n.mode & 1) for (me = n, te = n.child; te !== null; ) {
            for (oe = me = te; me !== null; ) {
              switch (ee = me, de = ee.child, ee.tag) {
                case 0:
                case 11:
                case 14:
                case 15:
                  ss(4, ee, ee.return);
                  break;
                case 1:
                  Qi(ee, ee.return);
                  var ye = ee.stateNode;
                  if (typeof ye.componentWillUnmount == "function") {
                    u = ee, s = ee.return;
                    try {
                      r = u, ye.props = r.memoizedProps, ye.state = r.memoizedState, ye.componentWillUnmount();
                    } catch (ge) {
                      st(u, s, ge);
                    }
                  }
                  break;
                case 5:
                  Qi(ee, ee.return);
                  break;
                case 22:
                  if (ee.memoizedState !== null) {
                    Gm(oe);
                    continue;
                  }
              }
              de !== null ? (de.return = ee, me = de) : Gm(oe);
            }
            te = te.sibling;
          }
          e: for (te = null, oe = n; ; ) {
            if (oe.tag === 5) {
              if (te === null) {
                te = oe;
                try {
                  p = oe.stateNode, Y ? (g = p.style, typeof g.setProperty == "function" ? g.setProperty("display", "none", "important") : g.display = "none") : (A = oe.stateNode, M = oe.memoizedProps.style, O = M != null && M.hasOwnProperty("display") ? M.display : null, A.style.display = Cp("display", O));
                } catch (ge) {
                  st(n, n.return, ge);
                }
              }
            } else if (oe.tag === 6) {
              if (te === null) try {
                oe.stateNode.nodeValue = Y ? "" : oe.memoizedProps;
              } catch (ge) {
                st(n, n.return, ge);
              }
            } else if ((oe.tag !== 22 && oe.tag !== 23 || oe.memoizedState === null || oe === n) && oe.child !== null) {
              oe.child.return = oe, oe = oe.child;
              continue;
            }
            if (oe === n) break e;
            for (; oe.sibling === null; ) {
              if (oe.return === null || oe.return === n) break e;
              te === oe && (te = null), oe = oe.return;
            }
            te === oe && (te = null), oe.sibling.return = oe.return, oe = oe.sibling;
          }
        }
        break;
      case 19:
        hn(r, n), Nn(n), u & 4 && Km(n);
        break;
      case 21:
        break;
      default:
        hn(
          r,
          n
        ), Nn(n);
    }
  }
  function Nn(n) {
    var r = n.flags;
    if (r & 2) {
      try {
        e: {
          for (var s = n.return; s !== null; ) {
            if (zm(s)) {
              var u = s;
              break e;
            }
            s = s.return;
          }
          throw Error(i(160));
        }
        switch (u.tag) {
          case 5:
            var p = u.stateNode;
            u.flags & 32 && (Hr(p, ""), u.flags &= -33);
            var g = Vm(n);
            Ic(n, g, p);
            break;
          case 3:
          case 4:
            var O = u.stateNode.containerInfo, A = Vm(n);
            Nc(n, A, O);
            break;
          default:
            throw Error(i(161));
        }
      } catch (M) {
        st(n, n.return, M);
      }
      n.flags &= -3;
    }
    r & 4096 && (n.flags &= -4097);
  }
  function Bw(n, r, s) {
    me = n, Hm(n);
  }
  function Hm(n, r, s) {
    for (var u = (n.mode & 1) !== 0; me !== null; ) {
      var p = me, g = p.child;
      if (p.tag === 22 && u) {
        var O = p.memoizedState !== null || Ba;
        if (!O) {
          var A = p.alternate, M = A !== null && A.memoizedState !== null || Nt;
          A = Ba;
          var Y = Nt;
          if (Ba = O, (Nt = M) && !Y) for (me = p; me !== null; ) O = me, M = O.child, O.tag === 22 && O.memoizedState !== null ? Ym(p) : M !== null ? (M.return = O, me = M) : Ym(p);
          for (; g !== null; ) me = g, Hm(g), g = g.sibling;
          me = p, Ba = A, Nt = Y;
        }
        qm(n);
      } else p.subtreeFlags & 8772 && g !== null ? (g.return = p, me = g) : qm(n);
    }
  }
  function qm(n) {
    for (; me !== null; ) {
      var r = me;
      if (r.flags & 8772) {
        var s = r.alternate;
        try {
          if (r.flags & 8772) switch (r.tag) {
            case 0:
            case 11:
            case 15:
              Nt || Ka(5, r);
              break;
            case 1:
              var u = r.stateNode;
              if (r.flags & 4 && !Nt) if (s === null) u.componentDidMount();
              else {
                var p = r.elementType === r.type ? s.memoizedProps : dn(r.type, s.memoizedProps);
                u.componentDidUpdate(p, s.memoizedState, u.__reactInternalSnapshotBeforeUpdate);
              }
              var g = r.updateQueue;
              g !== null && Gh(r, g, u);
              break;
            case 3:
              var O = r.updateQueue;
              if (O !== null) {
                if (s = null, r.child !== null) switch (r.child.tag) {
                  case 5:
                    s = r.child.stateNode;
                    break;
                  case 1:
                    s = r.child.stateNode;
                }
                Gh(r, O, s);
              }
              break;
            case 5:
              var A = r.stateNode;
              if (s === null && r.flags & 4) {
                s = A;
                var M = r.memoizedProps;
                switch (r.type) {
                  case "button":
                  case "input":
                  case "select":
                  case "textarea":
                    M.autoFocus && s.focus();
                    break;
                  case "img":
                    M.src && (s.src = M.src);
                }
              }
              break;
            case 6:
              break;
            case 4:
              break;
            case 12:
              break;
            case 13:
              if (r.memoizedState === null) {
                var Y = r.alternate;
                if (Y !== null) {
                  var te = Y.memoizedState;
                  if (te !== null) {
                    var oe = te.dehydrated;
                    oe !== null && Mo(oe);
                  }
                }
              }
              break;
            case 19:
            case 17:
            case 21:
            case 22:
            case 23:
            case 25:
              break;
            default:
              throw Error(i(163));
          }
          Nt || r.flags & 512 && Tc(r);
        } catch (ee) {
          st(r, r.return, ee);
        }
      }
      if (r === n) {
        me = null;
        break;
      }
      if (s = r.sibling, s !== null) {
        s.return = r.return, me = s;
        break;
      }
      me = r.return;
    }
  }
  function Gm(n) {
    for (; me !== null; ) {
      var r = me;
      if (r === n) {
        me = null;
        break;
      }
      var s = r.sibling;
      if (s !== null) {
        s.return = r.return, me = s;
        break;
      }
      me = r.return;
    }
  }
  function Ym(n) {
    for (; me !== null; ) {
      var r = me;
      try {
        switch (r.tag) {
          case 0:
          case 11:
          case 15:
            var s = r.return;
            try {
              Ka(4, r);
            } catch (M) {
              st(r, s, M);
            }
            break;
          case 1:
            var u = r.stateNode;
            if (typeof u.componentDidMount == "function") {
              var p = r.return;
              try {
                u.componentDidMount();
              } catch (M) {
                st(r, p, M);
              }
            }
            var g = r.return;
            try {
              Tc(r);
            } catch (M) {
              st(r, g, M);
            }
            break;
          case 5:
            var O = r.return;
            try {
              Tc(r);
            } catch (M) {
              st(r, O, M);
            }
        }
      } catch (M) {
        st(r, r.return, M);
      }
      if (r === n) {
        me = null;
        break;
      }
      var A = r.sibling;
      if (A !== null) {
        A.return = r.return, me = A;
        break;
      }
      me = r.return;
    }
  }
  var Kw = Math.ceil, Wa = T.ReactCurrentDispatcher, jc = T.ReactCurrentOwner, en = T.ReactCurrentBatchConfig, Re = 0, vt = null, ct = null, wt = 0, Yt = 0, Ji = yr(0), ht = 0, as = null, ti = 0, Ha = 0, Ac = 0, ls = null, Ut = null, xc = 0, Xi = 1 / 0, Zn = null, qa = !1, bc = null, Er = null, Ga = !1, $r = null, Ya = 0, us = 0, Fc = null, Qa = -1, Ja = 0;
  function xt() {
    return Re & 6 ? at() : Qa !== -1 ? Qa : Qa = at();
  }
  function Or(n) {
    return n.mode & 1 ? Re & 2 && wt !== 0 ? wt & -wt : kw.transition !== null ? (Ja === 0 && (Ja = Vp()), Ja) : (n = Ve, n !== 0 || (n = window.event, n = n === void 0 ? 16 : Jp(n.type)), n) : 1;
  }
  function mn(n, r, s, u) {
    if (50 < us) throw us = 0, Fc = null, Error(i(185));
    xo(n, s, u), (!(Re & 2) || n !== vt) && (n === vt && (!(Re & 2) && (Ha |= s), ht === 4 && Pr(n, wt)), zt(n, u), s === 1 && Re === 0 && !(r.mode & 1) && (Xi = at() + 500, Pa && vr()));
  }
  function zt(n, r) {
    var s = n.callbackNode;
    kS(n, r);
    var u = sa(n, n === vt ? wt : 0);
    if (u === 0) s !== null && Lp(s), n.callbackNode = null, n.callbackPriority = 0;
    else if (r = u & -u, n.callbackPriority !== r) {
      if (s != null && Lp(s), r === 1) n.tag === 0 ? Cw(Jm.bind(null, n)) : Rh(Jm.bind(null, n)), Ew(function() {
        !(Re & 6) && vr();
      }), s = null;
      else {
        switch (Bp(u)) {
          case 1:
            s = hu;
            break;
          case 4:
            s = Up;
            break;
          case 16:
            s = na;
            break;
          case 536870912:
            s = zp;
            break;
          default:
            s = na;
        }
        s = oy(s, Qm.bind(null, n));
      }
      n.callbackPriority = r, n.callbackNode = s;
    }
  }
  function Qm(n, r) {
    if (Qa = -1, Ja = 0, Re & 6) throw Error(i(327));
    var s = n.callbackNode;
    if (Zi() && n.callbackNode !== s) return null;
    var u = sa(n, n === vt ? wt : 0);
    if (u === 0) return null;
    if (u & 30 || u & n.expiredLanes || r) r = Xa(n, u);
    else {
      r = u;
      var p = Re;
      Re |= 2;
      var g = Zm();
      (vt !== n || wt !== r) && (Zn = null, Xi = at() + 500, ri(n, r));
      do
        try {
          qw();
          break;
        } catch (A) {
          Xm(n, A);
        }
      while (!0);
      Zu(), Wa.current = g, Re = p, ct !== null ? r = 0 : (vt = null, wt = 0, r = ht);
    }
    if (r !== 0) {
      if (r === 2 && (p = mu(n), p !== 0 && (u = p, r = Rc(n, p))), r === 1) throw s = as, ri(n, 0), Pr(n, u), zt(n, at()), s;
      if (r === 6) Pr(n, u);
      else {
        if (p = n.current.alternate, !(u & 30) && !Ww(p) && (r = Xa(n, u), r === 2 && (g = mu(n), g !== 0 && (u = g, r = Rc(n, g))), r === 1)) throw s = as, ri(n, 0), Pr(n, u), zt(n, at()), s;
        switch (n.finishedWork = p, n.finishedLanes = u, r) {
          case 0:
          case 1:
            throw Error(i(345));
          case 2:
            ii(n, Ut, Zn);
            break;
          case 3:
            if (Pr(n, u), (u & 130023424) === u && (r = xc + 500 - at(), 10 < r)) {
              if (sa(n, 0) !== 0) break;
              if (p = n.suspendedLanes, (p & u) !== u) {
                xt(), n.pingedLanes |= n.suspendedLanes & p;
                break;
              }
              n.timeoutHandle = Vu(ii.bind(null, n, Ut, Zn), r);
              break;
            }
            ii(n, Ut, Zn);
            break;
          case 4:
            if (Pr(n, u), (u & 4194240) === u) break;
            for (r = n.eventTimes, p = -1; 0 < u; ) {
              var O = 31 - un(u);
              g = 1 << O, O = r[O], O > p && (p = O), u &= ~g;
            }
            if (u = p, u = at() - u, u = (120 > u ? 120 : 480 > u ? 480 : 1080 > u ? 1080 : 1920 > u ? 1920 : 3e3 > u ? 3e3 : 4320 > u ? 4320 : 1960 * Kw(u / 1960)) - u, 10 < u) {
              n.timeoutHandle = Vu(ii.bind(null, n, Ut, Zn), u);
              break;
            }
            ii(n, Ut, Zn);
            break;
          case 5:
            ii(n, Ut, Zn);
            break;
          default:
            throw Error(i(329));
        }
      }
    }
    return zt(n, at()), n.callbackNode === s ? Qm.bind(null, n) : null;
  }
  function Rc(n, r) {
    var s = ls;
    return n.current.memoizedState.isDehydrated && (ri(n, r).flags |= 256), n = Xa(n, r), n !== 2 && (r = Ut, Ut = s, r !== null && Dc(r)), n;
  }
  function Dc(n) {
    Ut === null ? Ut = n : Ut.push.apply(Ut, n);
  }
  function Ww(n) {
    for (var r = n; ; ) {
      if (r.flags & 16384) {
        var s = r.updateQueue;
        if (s !== null && (s = s.stores, s !== null)) for (var u = 0; u < s.length; u++) {
          var p = s[u], g = p.getSnapshot;
          p = p.value;
          try {
            if (!cn(g(), p)) return !1;
          } catch {
            return !1;
          }
        }
      }
      if (s = r.child, r.subtreeFlags & 16384 && s !== null) s.return = r, r = s;
      else {
        if (r === n) break;
        for (; r.sibling === null; ) {
          if (r.return === null || r.return === n) return !0;
          r = r.return;
        }
        r.sibling.return = r.return, r = r.sibling;
      }
    }
    return !0;
  }
  function Pr(n, r) {
    for (r &= ~Ac, r &= ~Ha, n.suspendedLanes |= r, n.pingedLanes &= ~r, n = n.expirationTimes; 0 < r; ) {
      var s = 31 - un(r), u = 1 << s;
      n[s] = -1, r &= ~u;
    }
  }
  function Jm(n) {
    if (Re & 6) throw Error(i(327));
    Zi();
    var r = sa(n, 0);
    if (!(r & 1)) return zt(n, at()), null;
    var s = Xa(n, r);
    if (n.tag !== 0 && s === 2) {
      var u = mu(n);
      u !== 0 && (r = u, s = Rc(n, u));
    }
    if (s === 1) throw s = as, ri(n, 0), Pr(n, r), zt(n, at()), s;
    if (s === 6) throw Error(i(345));
    return n.finishedWork = n.current.alternate, n.finishedLanes = r, ii(n, Ut, Zn), zt(n, at()), null;
  }
  function Mc(n, r) {
    var s = Re;
    Re |= 1;
    try {
      return n(r);
    } finally {
      Re = s, Re === 0 && (Xi = at() + 500, Pa && vr());
    }
  }
  function ni(n) {
    $r !== null && $r.tag === 0 && !(Re & 6) && Zi();
    var r = Re;
    Re |= 1;
    var s = en.transition, u = Ve;
    try {
      if (en.transition = null, Ve = 1, n) return n();
    } finally {
      Ve = u, en.transition = s, Re = r, !(Re & 6) && vr();
    }
  }
  function Lc() {
    Yt = Ji.current, Qe(Ji);
  }
  function ri(n, r) {
    n.finishedWork = null, n.finishedLanes = 0;
    var s = n.timeoutHandle;
    if (s !== -1 && (n.timeoutHandle = -1, ww(s)), ct !== null) for (s = ct.return; s !== null; ) {
      var u = s;
      switch (Gu(u), u.tag) {
        case 1:
          u = u.type.childContextTypes, u != null && $a();
          break;
        case 3:
          Gi(), Qe(Dt), Qe(Ct), ac();
          break;
        case 5:
          oc(u);
          break;
        case 4:
          Gi();
          break;
        case 13:
          Qe(rt);
          break;
        case 19:
          Qe(rt);
          break;
        case 10:
          ec(u.type._context);
          break;
        case 22:
        case 23:
          Lc();
      }
      s = s.return;
    }
    if (vt = n, ct = n = Cr(n.current, null), wt = Yt = r, ht = 0, as = null, Ac = Ha = ti = 0, Ut = ls = null, Xr !== null) {
      for (r = 0; r < Xr.length; r++) if (s = Xr[r], u = s.interleaved, u !== null) {
        s.interleaved = null;
        var p = u.next, g = s.pending;
        if (g !== null) {
          var O = g.next;
          g.next = p, u.next = O;
        }
        s.pending = u;
      }
      Xr = null;
    }
    return n;
  }
  function Xm(n, r) {
    do {
      var s = ct;
      try {
        if (Zu(), Fa.current = La, Ra) {
          for (var u = it.memoizedState; u !== null; ) {
            var p = u.queue;
            p !== null && (p.pending = null), u = u.next;
          }
          Ra = !1;
        }
        if (ei = 0, gt = pt = it = null, ts = !1, ns = 0, jc.current = null, s === null || s.return === null) {
          ht = 1, as = r, ct = null;
          break;
        }
        e: {
          var g = n, O = s.return, A = s, M = r;
          if (r = wt, A.flags |= 32768, M !== null && typeof M == "object" && typeof M.then == "function") {
            var Y = M, te = A, oe = te.tag;
            if (!(te.mode & 1) && (oe === 0 || oe === 11 || oe === 15)) {
              var ee = te.alternate;
              ee ? (te.updateQueue = ee.updateQueue, te.memoizedState = ee.memoizedState, te.lanes = ee.lanes) : (te.updateQueue = null, te.memoizedState = null);
            }
            var de = $m(O);
            if (de !== null) {
              de.flags &= -257, Om(de, O, A, g, r), de.mode & 1 && Em(g, Y, r), r = de, M = Y;
              var ye = r.updateQueue;
              if (ye === null) {
                var ge = /* @__PURE__ */ new Set();
                ge.add(M), r.updateQueue = ge;
              } else ye.add(M);
              break e;
            } else {
              if (!(r & 1)) {
                Em(g, Y, r), Uc();
                break e;
              }
              M = Error(i(426));
            }
          } else if (tt && A.mode & 1) {
            var lt = $m(O);
            if (lt !== null) {
              !(lt.flags & 65536) && (lt.flags |= 256), Om(lt, O, A, g, r), Ju(Yi(M, A));
              break e;
            }
          }
          g = M = Yi(M, A), ht !== 4 && (ht = 2), ls === null ? ls = [g] : ls.push(g), g = O;
          do {
            switch (g.tag) {
              case 3:
                g.flags |= 65536, r &= -r, g.lanes |= r;
                var K = Sm(g, M, r);
                qh(g, K);
                break e;
              case 1:
                A = M;
                var L = g.type, W = g.stateNode;
                if (!(g.flags & 128) && (typeof L.getDerivedStateFromError == "function" || W !== null && typeof W.componentDidCatch == "function" && (Er === null || !Er.has(W)))) {
                  g.flags |= 65536, r &= -r, g.lanes |= r;
                  var ue = wm(g, A, r);
                  qh(g, ue);
                  break e;
                }
            }
            g = g.return;
          } while (g !== null);
        }
        ty(s);
      } catch (ve) {
        r = ve, ct === s && s !== null && (ct = s = s.return);
        continue;
      }
      break;
    } while (!0);
  }
  function Zm() {
    var n = Wa.current;
    return Wa.current = La, n === null ? La : n;
  }
  function Uc() {
    (ht === 0 || ht === 3 || ht === 2) && (ht = 4), vt === null || !(ti & 268435455) && !(Ha & 268435455) || Pr(vt, wt);
  }
  function Xa(n, r) {
    var s = Re;
    Re |= 2;
    var u = Zm();
    (vt !== n || wt !== r) && (Zn = null, ri(n, r));
    do
      try {
        Hw();
        break;
      } catch (p) {
        Xm(n, p);
      }
    while (!0);
    if (Zu(), Re = s, Wa.current = u, ct !== null) throw Error(i(261));
    return vt = null, wt = 0, ht;
  }
  function Hw() {
    for (; ct !== null; ) ey(ct);
  }
  function qw() {
    for (; ct !== null && !vS(); ) ey(ct);
  }
  function ey(n) {
    var r = iy(n.alternate, n, Yt);
    n.memoizedProps = n.pendingProps, r === null ? ty(n) : ct = r, jc.current = null;
  }
  function ty(n) {
    var r = n;
    do {
      var s = r.alternate;
      if (n = r.return, r.flags & 32768) {
        if (s = Uw(s, r), s !== null) {
          s.flags &= 32767, ct = s;
          return;
        }
        if (n !== null) n.flags |= 32768, n.subtreeFlags = 0, n.deletions = null;
        else {
          ht = 6, ct = null;
          return;
        }
      } else if (s = Lw(s, r, Yt), s !== null) {
        ct = s;
        return;
      }
      if (r = r.sibling, r !== null) {
        ct = r;
        return;
      }
      ct = r = n;
    } while (r !== null);
    ht === 0 && (ht = 5);
  }
  function ii(n, r, s) {
    var u = Ve, p = en.transition;
    try {
      en.transition = null, Ve = 1, Gw(n, r, s, u);
    } finally {
      en.transition = p, Ve = u;
    }
    return null;
  }
  function Gw(n, r, s, u) {
    do
      Zi();
    while ($r !== null);
    if (Re & 6) throw Error(i(327));
    s = n.finishedWork;
    var p = n.finishedLanes;
    if (s === null) return null;
    if (n.finishedWork = null, n.finishedLanes = 0, s === n.current) throw Error(i(177));
    n.callbackNode = null, n.callbackPriority = 0;
    var g = s.lanes | s.childLanes;
    if (TS(n, g), n === vt && (ct = vt = null, wt = 0), !(s.subtreeFlags & 2064) && !(s.flags & 2064) || Ga || (Ga = !0, oy(na, function() {
      return Zi(), null;
    })), g = (s.flags & 15990) !== 0, s.subtreeFlags & 15990 || g) {
      g = en.transition, en.transition = null;
      var O = Ve;
      Ve = 1;
      var A = Re;
      Re |= 4, jc.current = null, Vw(n, s), Wm(s, n), hw(Uu), ua = !!Lu, Uu = Lu = null, n.current = s, Bw(s), _S(), Re = A, Ve = O, en.transition = g;
    } else n.current = s;
    if (Ga && (Ga = !1, $r = n, Ya = p), g = n.pendingLanes, g === 0 && (Er = null), ES(s.stateNode), zt(n, at()), r !== null) for (u = n.onRecoverableError, s = 0; s < r.length; s++) p = r[s], u(p.value, { componentStack: p.stack, digest: p.digest });
    if (qa) throw qa = !1, n = bc, bc = null, n;
    return Ya & 1 && n.tag !== 0 && Zi(), g = n.pendingLanes, g & 1 ? n === Fc ? us++ : (us = 0, Fc = n) : us = 0, vr(), null;
  }
  function Zi() {
    if ($r !== null) {
      var n = Bp(Ya), r = en.transition, s = Ve;
      try {
        if (en.transition = null, Ve = 16 > n ? 16 : n, $r === null) var u = !1;
        else {
          if (n = $r, $r = null, Ya = 0, Re & 6) throw Error(i(331));
          var p = Re;
          for (Re |= 4, me = n.current; me !== null; ) {
            var g = me, O = g.child;
            if (me.flags & 16) {
              var A = g.deletions;
              if (A !== null) {
                for (var M = 0; M < A.length; M++) {
                  var Y = A[M];
                  for (me = Y; me !== null; ) {
                    var te = me;
                    switch (te.tag) {
                      case 0:
                      case 11:
                      case 15:
                        ss(8, te, g);
                    }
                    var oe = te.child;
                    if (oe !== null) oe.return = te, me = oe;
                    else for (; me !== null; ) {
                      te = me;
                      var ee = te.sibling, de = te.return;
                      if (Um(te), te === Y) {
                        me = null;
                        break;
                      }
                      if (ee !== null) {
                        ee.return = de, me = ee;
                        break;
                      }
                      me = de;
                    }
                  }
                }
                var ye = g.alternate;
                if (ye !== null) {
                  var ge = ye.child;
                  if (ge !== null) {
                    ye.child = null;
                    do {
                      var lt = ge.sibling;
                      ge.sibling = null, ge = lt;
                    } while (ge !== null);
                  }
                }
                me = g;
              }
            }
            if (g.subtreeFlags & 2064 && O !== null) O.return = g, me = O;
            else e: for (; me !== null; ) {
              if (g = me, g.flags & 2048) switch (g.tag) {
                case 0:
                case 11:
                case 15:
                  ss(9, g, g.return);
              }
              var K = g.sibling;
              if (K !== null) {
                K.return = g.return, me = K;
                break e;
              }
              me = g.return;
            }
          }
          var L = n.current;
          for (me = L; me !== null; ) {
            O = me;
            var W = O.child;
            if (O.subtreeFlags & 2064 && W !== null) W.return = O, me = W;
            else e: for (O = L; me !== null; ) {
              if (A = me, A.flags & 2048) try {
                switch (A.tag) {
                  case 0:
                  case 11:
                  case 15:
                    Ka(9, A);
                }
              } catch (ve) {
                st(A, A.return, ve);
              }
              if (A === O) {
                me = null;
                break e;
              }
              var ue = A.sibling;
              if (ue !== null) {
                ue.return = A.return, me = ue;
                break e;
              }
              me = A.return;
            }
          }
          if (Re = p, vr(), Pn && typeof Pn.onPostCommitFiberRoot == "function") try {
            Pn.onPostCommitFiberRoot(ra, n);
          } catch {
          }
          u = !0;
        }
        return u;
      } finally {
        Ve = s, en.transition = r;
      }
    }
    return !1;
  }
  function ny(n, r, s) {
    r = Yi(s, r), r = Sm(n, r, 1), n = Sr(n, r, 1), r = xt(), n !== null && (xo(n, 1, r), zt(n, r));
  }
  function st(n, r, s) {
    if (n.tag === 3) ny(n, n, s);
    else for (; r !== null; ) {
      if (r.tag === 3) {
        ny(r, n, s);
        break;
      } else if (r.tag === 1) {
        var u = r.stateNode;
        if (typeof r.type.getDerivedStateFromError == "function" || typeof u.componentDidCatch == "function" && (Er === null || !Er.has(u))) {
          n = Yi(s, n), n = wm(r, n, 1), r = Sr(r, n, 1), n = xt(), r !== null && (xo(r, 1, n), zt(r, n));
          break;
        }
      }
      r = r.return;
    }
  }
  function Yw(n, r, s) {
    var u = n.pingCache;
    u !== null && u.delete(r), r = xt(), n.pingedLanes |= n.suspendedLanes & s, vt === n && (wt & s) === s && (ht === 4 || ht === 3 && (wt & 130023424) === wt && 500 > at() - xc ? ri(n, 0) : Ac |= s), zt(n, r);
  }
  function ry(n, r) {
    r === 0 && (n.mode & 1 ? (r = oa, oa <<= 1, !(oa & 130023424) && (oa = 4194304)) : r = 1);
    var s = xt();
    n = Qn(n, r), n !== null && (xo(n, r, s), zt(n, s));
  }
  function Qw(n) {
    var r = n.memoizedState, s = 0;
    r !== null && (s = r.retryLane), ry(n, s);
  }
  function Jw(n, r) {
    var s = 0;
    switch (n.tag) {
      case 13:
        var u = n.stateNode, p = n.memoizedState;
        p !== null && (s = p.retryLane);
        break;
      case 19:
        u = n.stateNode;
        break;
      default:
        throw Error(i(314));
    }
    u !== null && u.delete(r), ry(n, s);
  }
  var iy;
  iy = function(n, r, s) {
    if (n !== null) if (n.memoizedProps !== r.pendingProps || Dt.current) Lt = !0;
    else {
      if (!(n.lanes & s) && !(r.flags & 128)) return Lt = !1, Mw(n, r, s);
      Lt = !!(n.flags & 131072);
    }
    else Lt = !1, tt && r.flags & 1048576 && Dh(r, ka, r.index);
    switch (r.lanes = 0, r.tag) {
      case 2:
        var u = r.type;
        Va(n, r), n = r.pendingProps;
        var p = zi(r, Ct.current);
        qi(r, s), p = cc(null, r, u, n, p, s);
        var g = fc();
        return r.flags |= 1, typeof p == "object" && p !== null && typeof p.render == "function" && p.$$typeof === void 0 ? (r.tag = 1, r.memoizedState = null, r.updateQueue = null, Mt(u) ? (g = !0, Oa(r)) : g = !1, r.memoizedState = p.state !== null && p.state !== void 0 ? p.state : null, rc(r), p.updater = Ua, r.stateNode = p, p._reactInternals = r, gc(r, u, n, s), r = wc(null, r, u, !0, g, s)) : (r.tag = 0, tt && g && qu(r), At(null, r, p, s), r = r.child), r;
      case 16:
        u = r.elementType;
        e: {
          switch (Va(n, r), n = r.pendingProps, p = u._init, u = p(u._payload), r.type = u, p = r.tag = Zw(u), n = dn(u, n), p) {
            case 0:
              r = Sc(null, r, u, n, s);
              break e;
            case 1:
              r = Im(null, r, u, n, s);
              break e;
            case 11:
              r = Pm(null, r, u, n, s);
              break e;
            case 14:
              r = Cm(null, r, u, dn(u.type, n), s);
              break e;
          }
          throw Error(i(
            306,
            u,
            ""
          ));
        }
        return r;
      case 0:
        return u = r.type, p = r.pendingProps, p = r.elementType === u ? p : dn(u, p), Sc(n, r, u, p, s);
      case 1:
        return u = r.type, p = r.pendingProps, p = r.elementType === u ? p : dn(u, p), Im(n, r, u, p, s);
      case 3:
        e: {
          if (jm(r), n === null) throw Error(i(387));
          u = r.pendingProps, g = r.memoizedState, p = g.element, Hh(n, r), xa(r, u, null, s);
          var O = r.memoizedState;
          if (u = O.element, g.isDehydrated) if (g = { element: u, isDehydrated: !1, cache: O.cache, pendingSuspenseBoundaries: O.pendingSuspenseBoundaries, transitions: O.transitions }, r.updateQueue.baseState = g, r.memoizedState = g, r.flags & 256) {
            p = Yi(Error(i(423)), r), r = Am(n, r, u, s, p);
            break e;
          } else if (u !== p) {
            p = Yi(Error(i(424)), r), r = Am(n, r, u, s, p);
            break e;
          } else for (Gt = mr(r.stateNode.containerInfo.firstChild), qt = r, tt = !0, fn = null, s = Kh(r, null, u, s), r.child = s; s; ) s.flags = s.flags & -3 | 4096, s = s.sibling;
          else {
            if (Ki(), u === p) {
              r = Xn(n, r, s);
              break e;
            }
            At(n, r, u, s);
          }
          r = r.child;
        }
        return r;
      case 5:
        return Yh(r), n === null && Qu(r), u = r.type, p = r.pendingProps, g = n !== null ? n.memoizedProps : null, O = p.children, zu(u, p) ? O = null : g !== null && zu(u, g) && (r.flags |= 32), Nm(n, r), At(n, r, O, s), r.child;
      case 6:
        return n === null && Qu(r), null;
      case 13:
        return xm(n, r, s);
      case 4:
        return ic(r, r.stateNode.containerInfo), u = r.pendingProps, n === null ? r.child = Wi(r, null, u, s) : At(n, r, u, s), r.child;
      case 11:
        return u = r.type, p = r.pendingProps, p = r.elementType === u ? p : dn(u, p), Pm(n, r, u, p, s);
      case 7:
        return At(n, r, r.pendingProps, s), r.child;
      case 8:
        return At(n, r, r.pendingProps.children, s), r.child;
      case 12:
        return At(n, r, r.pendingProps.children, s), r.child;
      case 10:
        e: {
          if (u = r.type._context, p = r.pendingProps, g = r.memoizedProps, O = p.value, He(Ia, u._currentValue), u._currentValue = O, g !== null) if (cn(g.value, O)) {
            if (g.children === p.children && !Dt.current) {
              r = Xn(n, r, s);
              break e;
            }
          } else for (g = r.child, g !== null && (g.return = r); g !== null; ) {
            var A = g.dependencies;
            if (A !== null) {
              O = g.child;
              for (var M = A.firstContext; M !== null; ) {
                if (M.context === u) {
                  if (g.tag === 1) {
                    M = Jn(-1, s & -s), M.tag = 2;
                    var Y = g.updateQueue;
                    if (Y !== null) {
                      Y = Y.shared;
                      var te = Y.pending;
                      te === null ? M.next = M : (M.next = te.next, te.next = M), Y.pending = M;
                    }
                  }
                  g.lanes |= s, M = g.alternate, M !== null && (M.lanes |= s), tc(
                    g.return,
                    s,
                    r
                  ), A.lanes |= s;
                  break;
                }
                M = M.next;
              }
            } else if (g.tag === 10) O = g.type === r.type ? null : g.child;
            else if (g.tag === 18) {
              if (O = g.return, O === null) throw Error(i(341));
              O.lanes |= s, A = O.alternate, A !== null && (A.lanes |= s), tc(O, s, r), O = g.sibling;
            } else O = g.child;
            if (O !== null) O.return = g;
            else for (O = g; O !== null; ) {
              if (O === r) {
                O = null;
                break;
              }
              if (g = O.sibling, g !== null) {
                g.return = O.return, O = g;
                break;
              }
              O = O.return;
            }
            g = O;
          }
          At(n, r, p.children, s), r = r.child;
        }
        return r;
      case 9:
        return p = r.type, u = r.pendingProps.children, qi(r, s), p = Xt(p), u = u(p), r.flags |= 1, At(n, r, u, s), r.child;
      case 14:
        return u = r.type, p = dn(u, r.pendingProps), p = dn(u.type, p), Cm(n, r, u, p, s);
      case 15:
        return km(n, r, r.type, r.pendingProps, s);
      case 17:
        return u = r.type, p = r.pendingProps, p = r.elementType === u ? p : dn(u, p), Va(n, r), r.tag = 1, Mt(u) ? (n = !0, Oa(r)) : n = !1, qi(r, s), vm(r, u, p), gc(r, u, p, s), wc(null, r, u, !0, n, s);
      case 19:
        return Fm(n, r, s);
      case 22:
        return Tm(n, r, s);
    }
    throw Error(i(156, r.tag));
  };
  function oy(n, r) {
    return Mp(n, r);
  }
  function Xw(n, r, s, u) {
    this.tag = n, this.key = s, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = r, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = u, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
  }
  function tn(n, r, s, u) {
    return new Xw(n, r, s, u);
  }
  function zc(n) {
    return n = n.prototype, !(!n || !n.isReactComponent);
  }
  function Zw(n) {
    if (typeof n == "function") return zc(n) ? 1 : 0;
    if (n != null) {
      if (n = n.$$typeof, n === H) return 11;
      if (n === ie) return 14;
    }
    return 2;
  }
  function Cr(n, r) {
    var s = n.alternate;
    return s === null ? (s = tn(n.tag, r, n.key, n.mode), s.elementType = n.elementType, s.type = n.type, s.stateNode = n.stateNode, s.alternate = n, n.alternate = s) : (s.pendingProps = r, s.type = n.type, s.flags = 0, s.subtreeFlags = 0, s.deletions = null), s.flags = n.flags & 14680064, s.childLanes = n.childLanes, s.lanes = n.lanes, s.child = n.child, s.memoizedProps = n.memoizedProps, s.memoizedState = n.memoizedState, s.updateQueue = n.updateQueue, r = n.dependencies, s.dependencies = r === null ? null : { lanes: r.lanes, firstContext: r.firstContext }, s.sibling = n.sibling, s.index = n.index, s.ref = n.ref, s;
  }
  function Za(n, r, s, u, p, g) {
    var O = 2;
    if (u = n, typeof n == "function") zc(n) && (O = 1);
    else if (typeof n == "string") O = 5;
    else e: switch (n) {
      case F:
        return oi(s.children, p, g, r);
      case V:
        O = 8, p |= 8;
        break;
      case U:
        return n = tn(12, s, r, p | 2), n.elementType = U, n.lanes = g, n;
      case q:
        return n = tn(13, s, r, p), n.elementType = q, n.lanes = g, n;
      case le:
        return n = tn(19, s, r, p), n.elementType = le, n.lanes = g, n;
      case pe:
        return el(s, p, g, r);
      default:
        if (typeof n == "object" && n !== null) switch (n.$$typeof) {
          case G:
            O = 10;
            break e;
          case Q:
            O = 9;
            break e;
          case H:
            O = 11;
            break e;
          case ie:
            O = 14;
            break e;
          case ne:
            O = 16, u = null;
            break e;
        }
        throw Error(i(130, n == null ? n : typeof n, ""));
    }
    return r = tn(O, s, r, p), r.elementType = n, r.type = u, r.lanes = g, r;
  }
  function oi(n, r, s, u) {
    return n = tn(7, n, u, r), n.lanes = s, n;
  }
  function el(n, r, s, u) {
    return n = tn(22, n, u, r), n.elementType = pe, n.lanes = s, n.stateNode = { isHidden: !1 }, n;
  }
  function Vc(n, r, s) {
    return n = tn(6, n, null, r), n.lanes = s, n;
  }
  function Bc(n, r, s) {
    return r = tn(4, n.children !== null ? n.children : [], n.key, r), r.lanes = s, r.stateNode = { containerInfo: n.containerInfo, pendingChildren: null, implementation: n.implementation }, r;
  }
  function e1(n, r, s, u, p) {
    this.tag = r, this.containerInfo = n, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = yu(0), this.expirationTimes = yu(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = yu(0), this.identifierPrefix = u, this.onRecoverableError = p, this.mutableSourceEagerHydrationData = null;
  }
  function Kc(n, r, s, u, p, g, O, A, M) {
    return n = new e1(n, r, s, A, M), r === 1 ? (r = 1, g === !0 && (r |= 8)) : r = 0, g = tn(3, null, null, r), n.current = g, g.stateNode = n, g.memoizedState = { element: u, isDehydrated: s, cache: null, transitions: null, pendingSuspenseBoundaries: null }, rc(g), n;
  }
  function t1(n, r, s) {
    var u = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
    return { $$typeof: x, key: u == null ? null : "" + u, children: n, containerInfo: r, implementation: s };
  }
  function sy(n) {
    if (!n) return gr;
    n = n._reactInternals;
    e: {
      if (qr(n) !== n || n.tag !== 1) throw Error(i(170));
      var r = n;
      do {
        switch (r.tag) {
          case 3:
            r = r.stateNode.context;
            break e;
          case 1:
            if (Mt(r.type)) {
              r = r.stateNode.__reactInternalMemoizedMergedChildContext;
              break e;
            }
        }
        r = r.return;
      } while (r !== null);
      throw Error(i(171));
    }
    if (n.tag === 1) {
      var s = n.type;
      if (Mt(s)) return bh(n, s, r);
    }
    return r;
  }
  function ay(n, r, s, u, p, g, O, A, M) {
    return n = Kc(s, u, !0, n, p, g, O, A, M), n.context = sy(null), s = n.current, u = xt(), p = Or(s), g = Jn(u, p), g.callback = r ?? null, Sr(s, g, p), n.current.lanes = p, xo(n, p, u), zt(n, u), n;
  }
  function tl(n, r, s, u) {
    var p = r.current, g = xt(), O = Or(p);
    return s = sy(s), r.context === null ? r.context = s : r.pendingContext = s, r = Jn(g, O), r.payload = { element: n }, u = u === void 0 ? null : u, u !== null && (r.callback = u), n = Sr(p, r, O), n !== null && (mn(n, p, O, g), Aa(n, p, O)), O;
  }
  function nl(n) {
    if (n = n.current, !n.child) return null;
    switch (n.child.tag) {
      case 5:
        return n.child.stateNode;
      default:
        return n.child.stateNode;
    }
  }
  function ly(n, r) {
    if (n = n.memoizedState, n !== null && n.dehydrated !== null) {
      var s = n.retryLane;
      n.retryLane = s !== 0 && s < r ? s : r;
    }
  }
  function Wc(n, r) {
    ly(n, r), (n = n.alternate) && ly(n, r);
  }
  function n1() {
    return null;
  }
  var uy = typeof reportError == "function" ? reportError : function(n) {
    console.error(n);
  };
  function Hc(n) {
    this._internalRoot = n;
  }
  rl.prototype.render = Hc.prototype.render = function(n) {
    var r = this._internalRoot;
    if (r === null) throw Error(i(409));
    tl(n, r, null, null);
  }, rl.prototype.unmount = Hc.prototype.unmount = function() {
    var n = this._internalRoot;
    if (n !== null) {
      this._internalRoot = null;
      var r = n.containerInfo;
      ni(function() {
        tl(null, n, null, null);
      }), r[Hn] = null;
    }
  };
  function rl(n) {
    this._internalRoot = n;
  }
  rl.prototype.unstable_scheduleHydration = function(n) {
    if (n) {
      var r = Hp();
      n = { blockedOn: null, target: n, priority: r };
      for (var s = 0; s < dr.length && r !== 0 && r < dr[s].priority; s++) ;
      dr.splice(s, 0, n), s === 0 && Yp(n);
    }
  };
  function qc(n) {
    return !(!n || n.nodeType !== 1 && n.nodeType !== 9 && n.nodeType !== 11);
  }
  function il(n) {
    return !(!n || n.nodeType !== 1 && n.nodeType !== 9 && n.nodeType !== 11 && (n.nodeType !== 8 || n.nodeValue !== " react-mount-point-unstable "));
  }
  function cy() {
  }
  function r1(n, r, s, u, p) {
    if (p) {
      if (typeof u == "function") {
        var g = u;
        u = function() {
          var Y = nl(O);
          g.call(Y);
        };
      }
      var O = ay(r, u, n, 0, null, !1, !1, "", cy);
      return n._reactRootContainer = O, n[Hn] = O.current, qo(n.nodeType === 8 ? n.parentNode : n), ni(), O;
    }
    for (; p = n.lastChild; ) n.removeChild(p);
    if (typeof u == "function") {
      var A = u;
      u = function() {
        var Y = nl(M);
        A.call(Y);
      };
    }
    var M = Kc(n, 0, !1, null, null, !1, !1, "", cy);
    return n._reactRootContainer = M, n[Hn] = M.current, qo(n.nodeType === 8 ? n.parentNode : n), ni(function() {
      tl(r, M, s, u);
    }), M;
  }
  function ol(n, r, s, u, p) {
    var g = s._reactRootContainer;
    if (g) {
      var O = g;
      if (typeof p == "function") {
        var A = p;
        p = function() {
          var M = nl(O);
          A.call(M);
        };
      }
      tl(r, O, n, p);
    } else O = r1(s, r, n, p, u);
    return nl(O);
  }
  Kp = function(n) {
    switch (n.tag) {
      case 3:
        var r = n.stateNode;
        if (r.current.memoizedState.isDehydrated) {
          var s = Ao(r.pendingLanes);
          s !== 0 && (gu(r, s | 1), zt(r, at()), !(Re & 6) && (Xi = at() + 500, vr()));
        }
        break;
      case 13:
        ni(function() {
          var u = Qn(n, 1);
          if (u !== null) {
            var p = xt();
            mn(u, n, 1, p);
          }
        }), Wc(n, 1);
    }
  }, vu = function(n) {
    if (n.tag === 13) {
      var r = Qn(n, 134217728);
      if (r !== null) {
        var s = xt();
        mn(r, n, 134217728, s);
      }
      Wc(n, 134217728);
    }
  }, Wp = function(n) {
    if (n.tag === 13) {
      var r = Or(n), s = Qn(n, r);
      if (s !== null) {
        var u = xt();
        mn(s, n, r, u);
      }
      Wc(n, r);
    }
  }, Hp = function() {
    return Ve;
  }, qp = function(n, r) {
    var s = Ve;
    try {
      return Ve = n, r();
    } finally {
      Ve = s;
    }
  }, cu = function(n, r, s) {
    switch (r) {
      case "input":
        if (Wt(n, s), r = s.name, s.type === "radio" && r != null) {
          for (s = n; s.parentNode; ) s = s.parentNode;
          for (s = s.querySelectorAll("input[name=" + JSON.stringify("" + r) + '][type="radio"]'), r = 0; r < s.length; r++) {
            var u = s[r];
            if (u !== n && u.form === n.form) {
              var p = Ea(u);
              if (!p) throw Error(i(90));
              nt(u), Wt(u, p);
            }
          }
        }
        break;
      case "textarea":
        Ti(n, s);
        break;
      case "select":
        r = s.value, r != null && On(n, !!s.multiple, r, !1);
    }
  }, jp = Mc, Ap = ni;
  var i1 = { usingClientEntryPoint: !1, Events: [Qo, Li, Ea, Np, Ip, Mc] }, cs = { findFiberByHostInstance: Gr, bundleType: 0, version: "18.3.1", rendererPackageName: "react-dom" }, o1 = { bundleType: cs.bundleType, version: cs.version, rendererPackageName: cs.rendererPackageName, rendererConfig: cs.rendererConfig, overrideHookState: null, overrideHookStateDeletePath: null, overrideHookStateRenamePath: null, overrideProps: null, overridePropsDeletePath: null, overridePropsRenamePath: null, setErrorHandler: null, setSuspenseHandler: null, scheduleUpdate: null, currentDispatcherRef: T.ReactCurrentDispatcher, findHostInstanceByFiber: function(n) {
    return n = Rp(n), n === null ? null : n.stateNode;
  }, findFiberByHostInstance: cs.findFiberByHostInstance || n1, findHostInstancesForRefresh: null, scheduleRefresh: null, scheduleRoot: null, setRefreshHandler: null, getCurrentFiber: null, reconcilerVersion: "18.3.1-next-f1338f8080-20240426" };
  if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
    var sl = __REACT_DEVTOOLS_GLOBAL_HOOK__;
    if (!sl.isDisabled && sl.supportsFiber) try {
      ra = sl.inject(o1), Pn = sl;
    } catch {
    }
  }
  return Vt.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = i1, Vt.createPortal = function(n, r) {
    var s = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
    if (!qc(r)) throw Error(i(200));
    return t1(n, r, null, s);
  }, Vt.createRoot = function(n, r) {
    if (!qc(n)) throw Error(i(299));
    var s = !1, u = "", p = uy;
    return r != null && (r.unstable_strictMode === !0 && (s = !0), r.identifierPrefix !== void 0 && (u = r.identifierPrefix), r.onRecoverableError !== void 0 && (p = r.onRecoverableError)), r = Kc(n, 1, !1, null, null, s, !1, u, p), n[Hn] = r.current, qo(n.nodeType === 8 ? n.parentNode : n), new Hc(r);
  }, Vt.findDOMNode = function(n) {
    if (n == null) return null;
    if (n.nodeType === 1) return n;
    var r = n._reactInternals;
    if (r === void 0)
      throw typeof n.render == "function" ? Error(i(188)) : (n = Object.keys(n).join(","), Error(i(268, n)));
    return n = Rp(r), n = n === null ? null : n.stateNode, n;
  }, Vt.flushSync = function(n) {
    return ni(n);
  }, Vt.hydrate = function(n, r, s) {
    if (!il(r)) throw Error(i(200));
    return ol(null, n, r, !0, s);
  }, Vt.hydrateRoot = function(n, r, s) {
    if (!qc(n)) throw Error(i(405));
    var u = s != null && s.hydratedSources || null, p = !1, g = "", O = uy;
    if (s != null && (s.unstable_strictMode === !0 && (p = !0), s.identifierPrefix !== void 0 && (g = s.identifierPrefix), s.onRecoverableError !== void 0 && (O = s.onRecoverableError)), r = ay(r, null, n, 1, s ?? null, p, !1, g, O), n[Hn] = r.current, qo(n), u) for (n = 0; n < u.length; n++) s = u[n], p = s._getVersion, p = p(s._source), r.mutableSourceEagerHydrationData == null ? r.mutableSourceEagerHydrationData = [s, p] : r.mutableSourceEagerHydrationData.push(
      s,
      p
    );
    return new rl(r);
  }, Vt.render = function(n, r, s) {
    if (!il(r)) throw Error(i(200));
    return ol(null, n, r, !1, s);
  }, Vt.unmountComponentAtNode = function(n) {
    if (!il(n)) throw Error(i(40));
    return n._reactRootContainer ? (ni(function() {
      ol(null, null, n, !1, function() {
        n._reactRootContainer = null, n[Hn] = null;
      });
    }), !0) : !1;
  }, Vt.unstable_batchedUpdates = Mc, Vt.unstable_renderSubtreeIntoContainer = function(n, r, s, u) {
    if (!il(s)) throw Error(i(200));
    if (n == null || n._reactInternals === void 0) throw Error(i(38));
    return ol(n, r, s, !1, u);
  }, Vt.version = "18.3.1-next-f1338f8080-20240426", Vt;
}
function pv() {
  if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function"))
    try {
      __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(pv);
    } catch (e) {
      console.error(e);
    }
}
pv(), dv.exports = d1();
var p1 = dv.exports, hv, my = p1;
hv = my.createRoot, my.hydrateRoot;
var mv = { exports: {} }, fs = {};
/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var yy;
function h1() {
  if (yy) return fs;
  yy = 1;
  var e = fe, t = Symbol.for("react.element"), i = Symbol.for("react.fragment"), o = Object.prototype.hasOwnProperty, a = e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, l = { key: !0, ref: !0, __self: !0, __source: !0 };
  function c(f, d, m) {
    var y, h = {}, S = null, $ = null;
    m !== void 0 && (S = "" + m), d.key !== void 0 && (S = "" + d.key), d.ref !== void 0 && ($ = d.ref);
    for (y in d) o.call(d, y) && !l.hasOwnProperty(y) && (h[y] = d[y]);
    if (f && f.defaultProps) for (y in d = f.defaultProps, d) h[y] === void 0 && (h[y] = d[y]);
    return { $$typeof: t, type: f, key: S, ref: $, props: h, _owner: a.current };
  }
  return fs.Fragment = i, fs.jsx = c, fs.jsxs = c, fs;
}
mv.exports = h1();
var D = mv.exports;
function xe(e) {
  return typeof e != "object" || e === null || typeof e.lastModified == "number" && typeof File < "u" && e instanceof File || typeof e.getMonth == "function" && typeof Date < "u" && e instanceof Date ? !1 : !Array.isArray(e);
}
function m1(e) {
  return e.additionalItems === !0 && console.warn("additionalItems=true is currently not supported"), xe(e.additionalItems);
}
function gy(e) {
  if (e === "")
    return;
  if (e === null)
    return null;
  if (/\.$/.test(e) || /\.0$/.test(e) || /\.\d*0$/.test(e))
    return e;
  const t = Number(e);
  return typeof t == "number" && !Number.isNaN(t) ? t : e;
}
const Fr = "__additional_property", Il = "additionalProperties", Ur = "allOf", be = "anyOf", on = "const", Vl = "default", Jf = "dependencies", y1 = "enum", $t = "__errors", Ke = "$id", g1 = "if", po = "items", v1 = "_$junk_option_schema_id$_", gl = "$name", Ne = "oneOf", Pf = "patternProperties", Me = "properties", Jc = "readonly", yv = "required", jl = "submitButtonOptions", Ze = "$ref", ys = "$schema", gv = "root", vv = "_", _1 = ["discriminator", "propertyName"], vy = "formContext", S1 = "layoutGridLookupMap", Xf = "__rjsf_additionalProperties", _v = "__rjsf_rootSchema", w1 = "ui:field", Zf = "ui:widget", Rr = "ui:options", Cf = "ui:globalOptions", E1 = "https://json-schema.org/draft/2019-09/schema", vl = "https://json-schema.org/draft/2020-12/schema";
function Ee(e = {}, t = {}) {
  return e ? Object.keys(e).filter((i) => i.indexOf("ui:") === 0).reduce((i, o) => {
    const a = e[o];
    return o === Zf && xe(a) ? (console.error("Setting options via ui:widget object is no longer supported, use ui:options instead"), i) : o === Rr && xe(a) ? { ...i, ...a } : { ...i, [o.substring(3)]: a };
  }, { ...t }) : { ...t };
}
function $1(e, t = {}, i) {
  if (!(e.additionalProperties || e.patternProperties))
    return !1;
  const { expandable: o = !0 } = Ee(t);
  return o === !1 ? o : e.maxProperties !== void 0 && i ? Object.keys(i).length < e.maxProperties : !0;
}
var Sv = typeof global == "object" && global && global.Object === Object && global, O1 = typeof self == "object" && self && self.Object === Object && self, Bn = Sv || O1 || Function("return this")(), sn = Bn.Symbol, wv = Object.prototype, P1 = wv.hasOwnProperty, C1 = wv.toString, ds = sn ? sn.toStringTag : void 0;
function k1(e) {
  var t = P1.call(e, ds), i = e[ds];
  try {
    e[ds] = void 0;
    var o = !0;
  } catch {
  }
  var a = C1.call(e);
  return o && (t ? e[ds] = i : delete e[ds]), a;
}
var T1 = Object.prototype, N1 = T1.toString;
function I1(e) {
  return N1.call(e);
}
var j1 = "[object Null]", A1 = "[object Undefined]", _y = sn ? sn.toStringTag : void 0;
function or(e) {
  return e == null ? e === void 0 ? A1 : j1 : _y && _y in Object(e) ? k1(e) : I1(e);
}
function Ev(e, t) {
  return function(i) {
    return e(t(i));
  };
}
var Bl = Ev(Object.getPrototypeOf, Object);
function an(e) {
  return e != null && typeof e == "object";
}
var x1 = "[object Object]", b1 = Function.prototype, F1 = Object.prototype, $v = b1.toString, R1 = F1.hasOwnProperty, D1 = $v.call(Object);
function zr(e) {
  if (!an(e) || or(e) != x1)
    return !1;
  var t = Bl(e);
  if (t === null)
    return !0;
  var i = R1.call(t, "constructor") && t.constructor;
  return typeof i == "function" && i instanceof i && $v.call(i) == D1;
}
function kf(e) {
  const t = {
    // We store the list of errors for this node in a property named __errors
    // to avoid name collision with a possible sub schema field named
    // 'errors' (see `utils.toErrorSchema`).
    [$t]: [],
    addError(i) {
      this[$t].push(i);
    }
  };
  if (Array.isArray(e))
    return e.reduce((i, o, a) => ({ ...i, [a]: kf(o) }), t);
  if (zr(e)) {
    const i = e;
    return Object.keys(i).reduce((o, a) => ({ ...o, [a]: kf(i[a]) }), t);
  }
  return t;
}
function M1() {
  this.__data__ = [], this.size = 0;
}
function Vs(e, t) {
  return e === t || e !== e && t !== t;
}
function Kl(e, t) {
  for (var i = e.length; i--; )
    if (Vs(e[i][0], t))
      return i;
  return -1;
}
var L1 = Array.prototype, U1 = L1.splice;
function z1(e) {
  var t = this.__data__, i = Kl(t, e);
  if (i < 0)
    return !1;
  var o = t.length - 1;
  return i == o ? t.pop() : U1.call(t, i, 1), --this.size, !0;
}
function V1(e) {
  var t = this.__data__, i = Kl(t, e);
  return i < 0 ? void 0 : t[i][1];
}
function B1(e) {
  return Kl(this.__data__, e) > -1;
}
function K1(e, t) {
  var i = this.__data__, o = Kl(i, e);
  return o < 0 ? (++this.size, i.push([e, t])) : i[o][1] = t, this;
}
function sr(e) {
  var t = -1, i = e == null ? 0 : e.length;
  for (this.clear(); ++t < i; ) {
    var o = e[t];
    this.set(o[0], o[1]);
  }
}
sr.prototype.clear = M1;
sr.prototype.delete = z1;
sr.prototype.get = V1;
sr.prototype.has = B1;
sr.prototype.set = K1;
function W1() {
  this.__data__ = new sr(), this.size = 0;
}
function H1(e) {
  var t = this.__data__, i = t.delete(e);
  return this.size = t.size, i;
}
function q1(e) {
  return this.__data__.get(e);
}
function G1(e) {
  return this.__data__.has(e);
}
function Fe(e) {
  var t = typeof e;
  return e != null && (t == "object" || t == "function");
}
var Y1 = "[object AsyncFunction]", Q1 = "[object Function]", J1 = "[object GeneratorFunction]", X1 = "[object Proxy]";
function Bs(e) {
  if (!Fe(e))
    return !1;
  var t = or(e);
  return t == Q1 || t == J1 || t == Y1 || t == X1;
}
var Xc = Bn["__core-js_shared__"], Sy = function() {
  var e = /[^.]+$/.exec(Xc && Xc.keys && Xc.keys.IE_PROTO || "");
  return e ? "Symbol(src)_1." + e : "";
}();
function Z1(e) {
  return !!Sy && Sy in e;
}
var eE = Function.prototype, tE = eE.toString;
function Si(e) {
  if (e != null) {
    try {
      return tE.call(e);
    } catch {
    }
    try {
      return e + "";
    } catch {
    }
  }
  return "";
}
var nE = /[\\^$.*+?()[\]{}|]/g, rE = /^\[object .+?Constructor\]$/, iE = Function.prototype, oE = Object.prototype, sE = iE.toString, aE = oE.hasOwnProperty, lE = RegExp(
  "^" + sE.call(aE).replace(nE, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
);
function uE(e) {
  if (!Fe(e) || Z1(e))
    return !1;
  var t = Bs(e) ? lE : rE;
  return t.test(Si(e));
}
function cE(e, t) {
  return e == null ? void 0 : e[t];
}
function wi(e, t) {
  var i = cE(e, t);
  return uE(i) ? i : void 0;
}
var Is = wi(Bn, "Map"), js = wi(Object, "create");
function fE() {
  this.__data__ = js ? js(null) : {}, this.size = 0;
}
function dE(e) {
  var t = this.has(e) && delete this.__data__[e];
  return this.size -= t ? 1 : 0, t;
}
var pE = "__lodash_hash_undefined__", hE = Object.prototype, mE = hE.hasOwnProperty;
function yE(e) {
  var t = this.__data__;
  if (js) {
    var i = t[e];
    return i === pE ? void 0 : i;
  }
  return mE.call(t, e) ? t[e] : void 0;
}
var gE = Object.prototype, vE = gE.hasOwnProperty;
function _E(e) {
  var t = this.__data__;
  return js ? t[e] !== void 0 : vE.call(t, e);
}
var SE = "__lodash_hash_undefined__";
function wE(e, t) {
  var i = this.__data__;
  return this.size += this.has(e) ? 0 : 1, i[e] = js && t === void 0 ? SE : t, this;
}
function hi(e) {
  var t = -1, i = e == null ? 0 : e.length;
  for (this.clear(); ++t < i; ) {
    var o = e[t];
    this.set(o[0], o[1]);
  }
}
hi.prototype.clear = fE;
hi.prototype.delete = dE;
hi.prototype.get = yE;
hi.prototype.has = _E;
hi.prototype.set = wE;
function EE() {
  this.size = 0, this.__data__ = {
    hash: new hi(),
    map: new (Is || sr)(),
    string: new hi()
  };
}
function $E(e) {
  var t = typeof e;
  return t == "string" || t == "number" || t == "symbol" || t == "boolean" ? e !== "__proto__" : e === null;
}
function Wl(e, t) {
  var i = e.__data__;
  return $E(t) ? i[typeof t == "string" ? "string" : "hash"] : i.map;
}
function OE(e) {
  var t = Wl(this, e).delete(e);
  return this.size -= t ? 1 : 0, t;
}
function PE(e) {
  return Wl(this, e).get(e);
}
function CE(e) {
  return Wl(this, e).has(e);
}
function kE(e, t) {
  var i = Wl(this, e), o = i.size;
  return i.set(e, t), this.size += i.size == o ? 0 : 1, this;
}
function ar(e) {
  var t = -1, i = e == null ? 0 : e.length;
  for (this.clear(); ++t < i; ) {
    var o = e[t];
    this.set(o[0], o[1]);
  }
}
ar.prototype.clear = EE;
ar.prototype.delete = OE;
ar.prototype.get = PE;
ar.prototype.has = CE;
ar.prototype.set = kE;
var TE = 200;
function NE(e, t) {
  var i = this.__data__;
  if (i instanceof sr) {
    var o = i.__data__;
    if (!Is || o.length < TE - 1)
      return o.push([e, t]), this.size = ++i.size, this;
    i = this.__data__ = new ar(o);
  }
  return i.set(e, t), this.size = i.size, this;
}
function Sn(e) {
  var t = this.__data__ = new sr(e);
  this.size = t.size;
}
Sn.prototype.clear = W1;
Sn.prototype.delete = H1;
Sn.prototype.get = q1;
Sn.prototype.has = G1;
Sn.prototype.set = NE;
var IE = "__lodash_hash_undefined__";
function jE(e) {
  return this.__data__.set(e, IE), this;
}
function AE(e) {
  return this.__data__.has(e);
}
function mi(e) {
  var t = -1, i = e == null ? 0 : e.length;
  for (this.__data__ = new ar(); ++t < i; )
    this.add(e[t]);
}
mi.prototype.add = mi.prototype.push = jE;
mi.prototype.has = AE;
function xE(e, t) {
  for (var i = -1, o = e == null ? 0 : e.length; ++i < o; )
    if (t(e[i], i, e))
      return !0;
  return !1;
}
function As(e, t) {
  return e.has(t);
}
var bE = 1, FE = 2;
function Ov(e, t, i, o, a, l) {
  var c = i & bE, f = e.length, d = t.length;
  if (f != d && !(c && d > f))
    return !1;
  var m = l.get(e), y = l.get(t);
  if (m && y)
    return m == t && y == e;
  var h = -1, S = !0, $ = i & FE ? new mi() : void 0;
  for (l.set(e, t), l.set(t, e); ++h < f; ) {
    var v = e[h], w = t[h];
    if (o)
      var _ = c ? o(w, v, h, t, e, l) : o(v, w, h, e, t, l);
    if (_ !== void 0) {
      if (_)
        continue;
      S = !1;
      break;
    }
    if ($) {
      if (!xE(t, function(E, k) {
        if (!As($, k) && (v === E || a(v, E, i, o, l)))
          return $.push(k);
      })) {
        S = !1;
        break;
      }
    } else if (!(v === w || a(v, w, i, o, l))) {
      S = !1;
      break;
    }
  }
  return l.delete(e), l.delete(t), S;
}
var Al = Bn.Uint8Array;
function RE(e) {
  var t = -1, i = Array(e.size);
  return e.forEach(function(o, a) {
    i[++t] = [a, o];
  }), i;
}
function ed(e) {
  var t = -1, i = Array(e.size);
  return e.forEach(function(o) {
    i[++t] = o;
  }), i;
}
var DE = 1, ME = 2, LE = "[object Boolean]", UE = "[object Date]", zE = "[object Error]", VE = "[object Map]", BE = "[object Number]", KE = "[object RegExp]", WE = "[object Set]", HE = "[object String]", qE = "[object Symbol]", GE = "[object ArrayBuffer]", YE = "[object DataView]", wy = sn ? sn.prototype : void 0, Zc = wy ? wy.valueOf : void 0;
function QE(e, t, i, o, a, l, c) {
  switch (i) {
    case YE:
      if (e.byteLength != t.byteLength || e.byteOffset != t.byteOffset)
        return !1;
      e = e.buffer, t = t.buffer;
    case GE:
      return !(e.byteLength != t.byteLength || !l(new Al(e), new Al(t)));
    case LE:
    case UE:
    case BE:
      return Vs(+e, +t);
    case zE:
      return e.name == t.name && e.message == t.message;
    case KE:
    case HE:
      return e == t + "";
    case VE:
      var f = RE;
    case WE:
      var d = o & DE;
      if (f || (f = ed), e.size != t.size && !d)
        return !1;
      var m = c.get(e);
      if (m)
        return m == t;
      o |= ME, c.set(e, t);
      var y = Ov(f(e), f(t), o, a, l, c);
      return c.delete(e), y;
    case qE:
      if (Zc)
        return Zc.call(e) == Zc.call(t);
  }
  return !1;
}
function td(e, t) {
  for (var i = -1, o = t.length, a = e.length; ++i < o; )
    e[a + i] = t[i];
  return e;
}
var yt = Array.isArray;
function Pv(e, t, i) {
  var o = t(e);
  return yt(e) ? o : td(o, i(e));
}
function JE(e, t) {
  for (var i = -1, o = e == null ? 0 : e.length, a = 0, l = []; ++i < o; ) {
    var c = e[i];
    t(c, i, e) && (l[a++] = c);
  }
  return l;
}
function Cv() {
  return [];
}
var XE = Object.prototype, ZE = XE.propertyIsEnumerable, Ey = Object.getOwnPropertySymbols, nd = Ey ? function(e) {
  return e == null ? [] : (e = Object(e), JE(Ey(e), function(t) {
    return ZE.call(e, t);
  }));
} : Cv;
function kv(e, t) {
  for (var i = -1, o = Array(e); ++i < e; )
    o[i] = t(i);
  return o;
}
var e$ = "[object Arguments]";
function $y(e) {
  return an(e) && or(e) == e$;
}
var Tv = Object.prototype, t$ = Tv.hasOwnProperty, n$ = Tv.propertyIsEnumerable, ho = $y(/* @__PURE__ */ function() {
  return arguments;
}()) ? $y : function(e) {
  return an(e) && t$.call(e, "callee") && !n$.call(e, "callee");
};
function r$() {
  return !1;
}
var Nv = typeof exports == "object" && exports && !exports.nodeType && exports, Oy = Nv && typeof module == "object" && module && !module.nodeType && module, i$ = Oy && Oy.exports === Nv, Py = i$ ? Bn.Buffer : void 0, o$ = Py ? Py.isBuffer : void 0, yi = o$ || r$, s$ = 9007199254740991, a$ = /^(?:0|[1-9]\d*)$/;
function Hl(e, t) {
  var i = typeof e;
  return t = t ?? s$, !!t && (i == "number" || i != "symbol" && a$.test(e)) && e > -1 && e % 1 == 0 && e < t;
}
var l$ = 9007199254740991;
function rd(e) {
  return typeof e == "number" && e > -1 && e % 1 == 0 && e <= l$;
}
var u$ = "[object Arguments]", c$ = "[object Array]", f$ = "[object Boolean]", d$ = "[object Date]", p$ = "[object Error]", h$ = "[object Function]", m$ = "[object Map]", y$ = "[object Number]", g$ = "[object Object]", v$ = "[object RegExp]", _$ = "[object Set]", S$ = "[object String]", w$ = "[object WeakMap]", E$ = "[object ArrayBuffer]", $$ = "[object DataView]", O$ = "[object Float32Array]", P$ = "[object Float64Array]", C$ = "[object Int8Array]", k$ = "[object Int16Array]", T$ = "[object Int32Array]", N$ = "[object Uint8Array]", I$ = "[object Uint8ClampedArray]", j$ = "[object Uint16Array]", A$ = "[object Uint32Array]", Je = {};
Je[O$] = Je[P$] = Je[C$] = Je[k$] = Je[T$] = Je[N$] = Je[I$] = Je[j$] = Je[A$] = !0;
Je[u$] = Je[c$] = Je[E$] = Je[f$] = Je[$$] = Je[d$] = Je[p$] = Je[h$] = Je[m$] = Je[y$] = Je[g$] = Je[v$] = Je[_$] = Je[S$] = Je[w$] = !1;
function x$(e) {
  return an(e) && rd(e.length) && !!Je[or(e)];
}
function id(e) {
  return function(t) {
    return e(t);
  };
}
var Iv = typeof exports == "object" && exports && !exports.nodeType && exports, ws = Iv && typeof module == "object" && module && !module.nodeType && module, b$ = ws && ws.exports === Iv, ef = b$ && Sv.process, mo = function() {
  try {
    var e = ws && ws.require && ws.require("util").types;
    return e || ef && ef.binding && ef.binding("util");
  } catch {
  }
}(), Cy = mo && mo.isTypedArray, Ks = Cy ? id(Cy) : x$, F$ = Object.prototype, R$ = F$.hasOwnProperty;
function jv(e, t) {
  var i = yt(e), o = !i && ho(e), a = !i && !o && yi(e), l = !i && !o && !a && Ks(e), c = i || o || a || l, f = c ? kv(e.length, String) : [], d = f.length;
  for (var m in e)
    (t || R$.call(e, m)) && !(c && // Safari 9 has enumerable `arguments.length` in strict mode.
    (m == "length" || // Node.js 0.10 has enumerable non-index properties on buffers.
    a && (m == "offset" || m == "parent") || // PhantomJS 2 has enumerable non-index properties on typed arrays.
    l && (m == "buffer" || m == "byteLength" || m == "byteOffset") || // Skip index properties.
    Hl(m, d))) && f.push(m);
  return f;
}
var D$ = Object.prototype;
function ql(e) {
  var t = e && e.constructor, i = typeof t == "function" && t.prototype || D$;
  return e === i;
}
var M$ = Ev(Object.keys, Object), L$ = Object.prototype, U$ = L$.hasOwnProperty;
function Av(e) {
  if (!ql(e))
    return M$(e);
  var t = [];
  for (var i in Object(e))
    U$.call(e, i) && i != "constructor" && t.push(i);
  return t;
}
function Ei(e) {
  return e != null && rd(e.length) && !Bs(e);
}
function vn(e) {
  return Ei(e) ? jv(e) : Av(e);
}
function Tf(e) {
  return Pv(e, vn, nd);
}
var z$ = 1, V$ = Object.prototype, B$ = V$.hasOwnProperty;
function K$(e, t, i, o, a, l) {
  var c = i & z$, f = Tf(e), d = f.length, m = Tf(t), y = m.length;
  if (d != y && !c)
    return !1;
  for (var h = d; h--; ) {
    var S = f[h];
    if (!(c ? S in t : B$.call(t, S)))
      return !1;
  }
  var $ = l.get(e), v = l.get(t);
  if ($ && v)
    return $ == t && v == e;
  var w = !0;
  l.set(e, t), l.set(t, e);
  for (var _ = c; ++h < d; ) {
    S = f[h];
    var E = e[S], k = t[S];
    if (o)
      var j = c ? o(k, E, S, t, e, l) : o(E, k, S, e, t, l);
    if (!(j === void 0 ? E === k || a(E, k, i, o, l) : j)) {
      w = !1;
      break;
    }
    _ || (_ = S == "constructor");
  }
  if (w && !_) {
    var T = e.constructor, N = t.constructor;
    T != N && "constructor" in e && "constructor" in t && !(typeof T == "function" && T instanceof T && typeof N == "function" && N instanceof N) && (w = !1);
  }
  return l.delete(e), l.delete(t), w;
}
var Nf = wi(Bn, "DataView"), If = wi(Bn, "Promise"), ao = wi(Bn, "Set"), jf = wi(Bn, "WeakMap"), ky = "[object Map]", W$ = "[object Object]", Ty = "[object Promise]", Ny = "[object Set]", Iy = "[object WeakMap]", jy = "[object DataView]", H$ = Si(Nf), q$ = Si(Is), G$ = Si(If), Y$ = Si(ao), Q$ = Si(jf), rn = or;
(Nf && rn(new Nf(new ArrayBuffer(1))) != jy || Is && rn(new Is()) != ky || If && rn(If.resolve()) != Ty || ao && rn(new ao()) != Ny || jf && rn(new jf()) != Iy) && (rn = function(e) {
  var t = or(e), i = t == W$ ? e.constructor : void 0, o = i ? Si(i) : "";
  if (o)
    switch (o) {
      case H$:
        return jy;
      case q$:
        return ky;
      case G$:
        return Ty;
      case Y$:
        return Ny;
      case Q$:
        return Iy;
    }
  return t;
});
var J$ = 1, Ay = "[object Arguments]", xy = "[object Array]", al = "[object Object]", X$ = Object.prototype, by = X$.hasOwnProperty;
function Z$(e, t, i, o, a, l) {
  var c = yt(e), f = yt(t), d = c ? xy : rn(e), m = f ? xy : rn(t);
  d = d == Ay ? al : d, m = m == Ay ? al : m;
  var y = d == al, h = m == al, S = d == m;
  if (S && yi(e)) {
    if (!yi(t))
      return !1;
    c = !0, y = !1;
  }
  if (S && !y)
    return l || (l = new Sn()), c || Ks(e) ? Ov(e, t, i, o, a, l) : QE(e, t, d, i, o, a, l);
  if (!(i & J$)) {
    var $ = y && by.call(e, "__wrapped__"), v = h && by.call(t, "__wrapped__");
    if ($ || v) {
      var w = $ ? e.value() : e, _ = v ? t.value() : t;
      return l || (l = new Sn()), a(w, _, i, o, l);
    }
  }
  return S ? (l || (l = new Sn()), K$(e, t, i, o, a, l)) : !1;
}
function Ws(e, t, i, o, a) {
  return e === t ? !0 : e == null || t == null || !an(e) && !an(t) ? e !== e && t !== t : Z$(e, t, i, o, Ws, a);
}
function eO(e, t, i) {
  i = typeof i == "function" ? i : void 0;
  var o = i ? i(e, t) : void 0;
  return o === void 0 ? Ws(e, t, void 0, i) : !!o;
}
function Ge(e, t) {
  return eO(e, t, (i, o) => {
    if (typeof i == "function" && typeof o == "function")
      return !0;
  });
}
var tO = "[object Symbol]";
function Hs(e) {
  return typeof e == "symbol" || an(e) && or(e) == tO;
}
var nO = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, rO = /^\w*$/;
function od(e, t) {
  if (yt(e))
    return !1;
  var i = typeof e;
  return i == "number" || i == "symbol" || i == "boolean" || e == null || Hs(e) ? !0 : rO.test(e) || !nO.test(e) || t != null && e in Object(t);
}
var iO = "Expected a function";
function sd(e, t) {
  if (typeof e != "function" || t != null && typeof t != "function")
    throw new TypeError(iO);
  var i = function() {
    var o = arguments, a = t ? t.apply(this, o) : o[0], l = i.cache;
    if (l.has(a))
      return l.get(a);
    var c = e.apply(this, o);
    return i.cache = l.set(a, c) || l, c;
  };
  return i.cache = new (sd.Cache || ar)(), i;
}
sd.Cache = ar;
var oO = 500;
function sO(e) {
  var t = sd(e, function(o) {
    return i.size === oO && i.clear(), o;
  }), i = t.cache;
  return t;
}
var aO = /[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g, lO = /\\(\\)?/g, xv = sO(function(e) {
  var t = [];
  return e.charCodeAt(0) === 46 && t.push(""), e.replace(aO, function(i, o, a, l) {
    t.push(a ? l.replace(lO, "$1") : o || i);
  }), t;
});
function So(e, t) {
  for (var i = -1, o = e == null ? 0 : e.length, a = Array(o); ++i < o; )
    a[i] = t(e[i], i, e);
  return a;
}
var Fy = sn ? sn.prototype : void 0, Ry = Fy ? Fy.toString : void 0;
function bv(e) {
  if (typeof e == "string")
    return e;
  if (yt(e))
    return So(e, bv) + "";
  if (Hs(e))
    return Ry ? Ry.call(e) : "";
  var t = e + "";
  return t == "0" && 1 / e == -1 / 0 ? "-0" : t;
}
function ad(e) {
  return e == null ? "" : bv(e);
}
function wo(e, t) {
  return yt(e) ? e : od(e, t) ? [e] : xv(ad(e));
}
function $i(e) {
  if (typeof e == "string" || Hs(e))
    return e;
  var t = e + "";
  return t == "0" && 1 / e == -1 / 0 ? "-0" : t;
}
function Gl(e, t) {
  t = wo(t, e);
  for (var i = 0, o = t.length; e != null && i < o; )
    e = e[$i(t[i++])];
  return i && i == o ? e : void 0;
}
function re(e, t, i) {
  var o = e == null ? void 0 : Gl(e, t);
  return o === void 0 ? i : o;
}
var uO = Object.prototype, cO = uO.hasOwnProperty;
function fO(e, t) {
  return e != null && cO.call(e, t);
}
function Fv(e, t, i) {
  t = wo(t, e);
  for (var o = -1, a = t.length, l = !1; ++o < a; ) {
    var c = $i(t[o]);
    if (!(l = e != null && i(e, c)))
      break;
    e = e[c];
  }
  return l || ++o != a ? l : (a = e == null ? 0 : e.length, !!a && rd(a) && Hl(c, a) && (yt(e) || ho(e)));
}
function Ae(e, t) {
  return e != null && Fv(e, t, fO);
}
function xs(e, t) {
  return Ws(e, t);
}
var xl = function() {
  try {
    var e = wi(Object, "defineProperty");
    return e({}, "", {}), e;
  } catch {
  }
}();
function ld(e, t, i) {
  t == "__proto__" && xl ? xl(e, t, {
    configurable: !0,
    enumerable: !0,
    value: i,
    writable: !0
  }) : e[t] = i;
}
var dO = Object.prototype, pO = dO.hasOwnProperty;
function ud(e, t, i) {
  var o = e[t];
  (!(pO.call(e, t) && Vs(o, i)) || i === void 0 && !(t in e)) && ld(e, t, i);
}
function cd(e, t, i, o) {
  if (!Fe(e))
    return e;
  t = wo(t, e);
  for (var a = -1, l = t.length, c = l - 1, f = e; f != null && ++a < l; ) {
    var d = $i(t[a]), m = i;
    if (d === "__proto__" || d === "constructor" || d === "prototype")
      return e;
    if (a != c) {
      var y = f[d];
      m = o ? o(y, d, f) : void 0, m === void 0 && (m = Fe(y) ? y : Hl(t[a + 1]) ? [] : {});
    }
    ud(f, d, m), f = f[d];
  }
  return e;
}
function Be(e, t, i) {
  return e == null ? e : cd(e, t, i);
}
function Yl(e) {
  return e;
}
function Rv(e) {
  return typeof e == "function" ? e : Yl;
}
var hO = /\s/;
function mO(e) {
  for (var t = e.length; t-- && hO.test(e.charAt(t)); )
    ;
  return t;
}
var yO = /^\s+/;
function gO(e) {
  return e && e.slice(0, mO(e) + 1).replace(yO, "");
}
var Dy = NaN, vO = /^[-+]0x[0-9a-f]+$/i, _O = /^0b[01]+$/i, SO = /^0o[0-7]+$/i, wO = parseInt;
function EO(e) {
  if (typeof e == "number")
    return e;
  if (Hs(e))
    return Dy;
  if (Fe(e)) {
    var t = typeof e.valueOf == "function" ? e.valueOf() : e;
    e = Fe(t) ? t + "" : t;
  }
  if (typeof e != "string")
    return e === 0 ? e : +e;
  e = gO(e);
  var i = _O.test(e);
  return i || SO.test(e) ? wO(e.slice(2), i ? 2 : 8) : vO.test(e) ? Dy : +e;
}
var My = 1 / 0, $O = 17976931348623157e292;
function OO(e) {
  if (!e)
    return e === 0 ? e : 0;
  if (e = EO(e), e === My || e === -My) {
    var t = e < 0 ? -1 : 1;
    return t * $O;
  }
  return e === e ? e : 0;
}
function Dv(e) {
  var t = OO(e), i = t % 1;
  return t === t ? i ? t - i : t : 0;
}
var PO = 9007199254740991, tf = 4294967295, CO = Math.min;
function Mv(e, t) {
  if (e = Dv(e), e < 1 || e > PO)
    return [];
  var i = tf, o = CO(e, tf);
  t = Rv(t), e -= tf;
  for (var a = kv(o, t); ++i < e; )
    t(i);
  return a;
}
function fd(e, t) {
  for (var i = -1, o = e == null ? 0 : e.length; ++i < o && t(e[i], i, e) !== !1; )
    ;
  return e;
}
var Ly = Object.create, Lv = /* @__PURE__ */ function() {
  function e() {
  }
  return function(t) {
    if (!Fe(t))
      return {};
    if (Ly)
      return Ly(t);
    e.prototype = t;
    var i = new e();
    return e.prototype = void 0, i;
  };
}();
function kO(e) {
  return function(t, i, o) {
    for (var a = -1, l = Object(t), c = o(t), f = c.length; f--; ) {
      var d = c[++a];
      if (i(l[d], d, l) === !1)
        break;
    }
    return t;
  };
}
var Uv = kO();
function zv(e, t) {
  return e && Uv(e, t, vn);
}
var TO = 1, NO = 2;
function IO(e, t, i, o) {
  var a = i.length, l = a;
  if (e == null)
    return !l;
  for (e = Object(e); a--; ) {
    var c = i[a];
    if (c[2] ? c[1] !== e[c[0]] : !(c[0] in e))
      return !1;
  }
  for (; ++a < l; ) {
    c = i[a];
    var f = c[0], d = e[f], m = c[1];
    if (c[2]) {
      if (d === void 0 && !(f in e))
        return !1;
    } else {
      var y = new Sn(), h;
      if (!(h === void 0 ? Ws(m, d, TO | NO, o, y) : h))
        return !1;
    }
  }
  return !0;
}
function Vv(e) {
  return e === e && !Fe(e);
}
function jO(e) {
  for (var t = vn(e), i = t.length; i--; ) {
    var o = t[i], a = e[o];
    t[i] = [o, a, Vv(a)];
  }
  return t;
}
function Bv(e, t) {
  return function(i) {
    return i == null ? !1 : i[e] === t && (t !== void 0 || e in Object(i));
  };
}
function AO(e) {
  var t = jO(e);
  return t.length == 1 && t[0][2] ? Bv(t[0][0], t[0][1]) : function(i) {
    return i === e || IO(i, e, t);
  };
}
function xO(e, t) {
  return e != null && t in Object(e);
}
function Kv(e, t) {
  return e != null && Fv(e, t, xO);
}
var bO = 1, FO = 2;
function RO(e, t) {
  return od(e) && Vv(t) ? Bv($i(e), t) : function(i) {
    var o = re(i, e);
    return o === void 0 && o === t ? Kv(i, e) : Ws(t, o, bO | FO);
  };
}
function DO(e) {
  return function(t) {
    return t == null ? void 0 : t[e];
  };
}
function MO(e) {
  return function(t) {
    return Gl(t, e);
  };
}
function LO(e) {
  return od(e) ? DO($i(e)) : MO(e);
}
function dd(e) {
  return typeof e == "function" ? e : e == null ? Yl : typeof e == "object" ? yt(e) ? RO(e[0], e[1]) : AO(e) : LO(e);
}
function UO(e, t, i) {
  var o = yt(e), a = o || yi(e) || Ks(e);
  if (t = dd(t), i == null) {
    var l = e && e.constructor;
    a ? i = o ? new l() : [] : Fe(e) ? i = Bs(l) ? Lv(Bl(e)) : {} : i = {};
  }
  return (a ? fd : zv)(e, function(c, f, d) {
    return t(i, c, f, d);
  }), i;
}
function Af(e, t, i) {
  (i !== void 0 && !Vs(e[t], i) || i === void 0 && !(t in e)) && ld(e, t, i);
}
var Wv = typeof exports == "object" && exports && !exports.nodeType && exports, Uy = Wv && typeof module == "object" && module && !module.nodeType && module, zO = Uy && Uy.exports === Wv, zy = zO ? Bn.Buffer : void 0, Vy = zy ? zy.allocUnsafe : void 0;
function Hv(e, t) {
  if (t)
    return e.slice();
  var i = e.length, o = Vy ? Vy(i) : new e.constructor(i);
  return e.copy(o), o;
}
function pd(e) {
  var t = new e.constructor(e.byteLength);
  return new Al(t).set(new Al(e)), t;
}
function qv(e, t) {
  var i = t ? pd(e.buffer) : e.buffer;
  return new e.constructor(i, e.byteOffset, e.length);
}
function hd(e, t) {
  var i = -1, o = e.length;
  for (t || (t = Array(o)); ++i < o; )
    t[i] = e[i];
  return t;
}
function Gv(e) {
  return typeof e.constructor == "function" && !ql(e) ? Lv(Bl(e)) : {};
}
function bs(e) {
  return an(e) && Ei(e);
}
function xf(e, t) {
  if (!(t === "constructor" && typeof e[t] == "function") && t != "__proto__")
    return e[t];
}
function Eo(e, t, i, o) {
  var a = !i;
  i || (i = {});
  for (var l = -1, c = t.length; ++l < c; ) {
    var f = t[l], d = void 0;
    d === void 0 && (d = e[f]), a ? ld(i, f, d) : ud(i, f, d);
  }
  return i;
}
function VO(e) {
  var t = [];
  if (e != null)
    for (var i in Object(e))
      t.push(i);
  return t;
}
var BO = Object.prototype, KO = BO.hasOwnProperty;
function WO(e) {
  if (!Fe(e))
    return VO(e);
  var t = ql(e), i = [];
  for (var o in e)
    o == "constructor" && (t || !KO.call(e, o)) || i.push(o);
  return i;
}
function qs(e) {
  return Ei(e) ? jv(e, !0) : WO(e);
}
function HO(e) {
  return Eo(e, qs(e));
}
function qO(e, t, i, o, a, l, c) {
  var f = xf(e, i), d = xf(t, i), m = c.get(d);
  if (m) {
    Af(e, i, m);
    return;
  }
  var y = l ? l(f, d, i + "", e, t, c) : void 0, h = y === void 0;
  if (h) {
    var S = yt(d), $ = !S && yi(d), v = !S && !$ && Ks(d);
    y = d, S || $ || v ? yt(f) ? y = f : bs(f) ? y = hd(f) : $ ? (h = !1, y = Hv(d, !0)) : v ? (h = !1, y = qv(d, !0)) : y = [] : zr(d) || ho(d) ? (y = f, ho(f) ? y = HO(f) : (!Fe(f) || Bs(f)) && (y = Gv(d))) : h = !1;
  }
  h && (c.set(d, y), a(y, d, o, l, c), c.delete(d)), Af(e, i, y);
}
function Yv(e, t, i, o, a) {
  e !== t && Uv(t, function(l, c) {
    if (a || (a = new Sn()), Fe(l))
      qO(e, t, c, i, Yv, o, a);
    else {
      var f = o ? o(xf(e, c), l, c + "", e, t, a) : void 0;
      f === void 0 && (f = l), Af(e, c, f);
    }
  }, qs);
}
function GO(e, t, i) {
  switch (i.length) {
    case 0:
      return e.call(t);
    case 1:
      return e.call(t, i[0]);
    case 2:
      return e.call(t, i[0], i[1]);
    case 3:
      return e.call(t, i[0], i[1], i[2]);
  }
  return e.apply(t, i);
}
var By = Math.max;
function Qv(e, t, i) {
  return t = By(t === void 0 ? e.length - 1 : t, 0), function() {
    for (var o = arguments, a = -1, l = By(o.length - t, 0), c = Array(l); ++a < l; )
      c[a] = o[t + a];
    a = -1;
    for (var f = Array(t + 1); ++a < t; )
      f[a] = o[a];
    return f[t] = i(c), GO(e, this, f);
  };
}
function YO(e) {
  return function() {
    return e;
  };
}
var QO = xl ? function(e, t) {
  return xl(e, "toString", {
    configurable: !0,
    enumerable: !1,
    value: YO(t),
    writable: !0
  });
} : Yl, JO = 800, XO = 16, ZO = Date.now;
function eP(e) {
  var t = 0, i = 0;
  return function() {
    var o = ZO(), a = XO - (o - i);
    if (i = o, a > 0) {
      if (++t >= JO)
        return arguments[0];
    } else
      t = 0;
    return e.apply(void 0, arguments);
  };
}
var Jv = eP(QO);
function Ql(e, t) {
  return Jv(Qv(e, t, Yl), e + "");
}
function tP(e, t, i) {
  if (!Fe(i))
    return !1;
  var o = typeof t;
  return (o == "number" ? Ei(i) && Hl(t, i.length) : o == "string" && t in i) ? Vs(i[t], e) : !1;
}
function nP(e) {
  return Ql(function(t, i) {
    var o = -1, a = i.length, l = a > 1 ? i[a - 1] : void 0, c = a > 2 ? i[2] : void 0;
    for (l = e.length > 3 && typeof l == "function" ? (a--, l) : void 0, c && tP(i[0], i[1], c) && (l = a < 3 ? void 0 : l, a = 1), t = Object(t); ++o < a; ) {
      var f = i[o];
      f && e(t, f, o, l);
    }
    return t;
  });
}
var rP = nP(function(e, t, i) {
  Yv(e, t, i);
}), Ky = sn ? sn.isConcatSpreadable : void 0;
function iP(e) {
  return yt(e) || ho(e) || !!(Ky && e && e[Ky]);
}
function Gs(e, t, i, o, a) {
  var l = -1, c = e.length;
  for (i || (i = iP), a || (a = []); ++l < c; ) {
    var f = e[l];
    t > 0 && i(f) ? t > 1 ? Gs(f, t - 1, i, o, a) : td(a, f) : o || (a[a.length] = f);
  }
  return a;
}
var oP = 1 / 0;
function sP(e) {
  var t = e == null ? 0 : e.length;
  return t ? Gs(e, oP) : [];
}
function aP(e, t, i, o) {
  for (var a = e.length, l = i + -1; ++l < a; )
    if (t(e[l], l, e))
      return l;
  return -1;
}
function lP(e) {
  return e !== e;
}
function uP(e, t, i) {
  for (var o = i - 1, a = e.length; ++o < a; )
    if (e[o] === t)
      return o;
  return -1;
}
function Xv(e, t, i) {
  return t === t ? uP(e, t, i) : aP(e, lP, i);
}
function md(e, t) {
  var i = e == null ? 0 : e.length;
  return !!i && Xv(e, t, 0) > -1;
}
function _l() {
}
var cP = 1 / 0, fP = ao && 1 / ed(new ao([, -0]))[1] == cP ? function(e) {
  return new ao(e);
} : _l, dP = 200;
function Zv(e, t, i) {
  var o = -1, a = md, l = e.length, c = !0, f = [], d = f;
  if (l >= dP) {
    var m = fP(e);
    if (m)
      return ed(m);
    c = !1, a = As, d = new mi();
  } else
    d = f;
  e:
    for (; ++o < l; ) {
      var y = e[o], h = y;
      if (y = y !== 0 ? y : 0, c && h === h) {
        for (var S = d.length; S--; )
          if (d[S] === h)
            continue e;
        f.push(y);
      } else a(d, h, i) || (d !== f && d.push(h), f.push(y));
    }
  return f;
}
function e0(e) {
  return e && e.length ? Zv(e) : [];
}
var pP = "[object Map]", hP = "[object Set]", mP = Object.prototype, yP = mP.hasOwnProperty;
function dt(e) {
  if (e == null)
    return !0;
  if (Ei(e) && (yt(e) || typeof e == "string" || typeof e.splice == "function" || yi(e) || Ks(e) || ho(e)))
    return !e.length;
  var t = rn(e);
  if (t == pP || t == hP)
    return !e.size;
  if (ql(e))
    return !Av(e).length;
  for (var i in e)
    if (yP.call(e, i))
      return !1;
  return !0;
}
const gP = Object.prototype;
function gs(e) {
  for (const t in e)
    if (gP.hasOwnProperty.call(e, t))
      return !1;
  return !0;
}
const vP = [
  "array",
  "boolean",
  "integer",
  "null",
  "number",
  "object",
  "string"
];
new Set(vP);
const _P = [
  "$defs",
  "definitions",
  "properties",
  "patternProperties",
  "dependencies"
];
new Set(_P);
const SP = [
  "items",
  "allOf",
  "oneOf",
  "anyOf"
];
new Set(SP);
const wP = [
  "items",
  "additionalItems",
  "additionalProperties",
  "propertyNames",
  "contains",
  "if",
  "then",
  "else",
  "not"
];
new Set(wP);
function Sl(e) {
  return typeof e == "object";
}
function An(e) {
  return Sl(e) ? gs(e) : e === !0;
}
function so(e, t) {
  return e < t ? -1 : e > t ? 1 : 0;
}
function nf(e, t) {
  const i = e.length;
  if (i === 0)
    return t;
  let o = t.length;
  if (o === 0)
    return e;
  if (i < o) {
    const l = e;
    e = t, t = l, o = i;
  }
  const a = new Set(e);
  for (let l = 0; l < o; l++)
    a.add(t[l]);
  return Array.from(a);
}
function EP(e, t) {
  const i = [];
  if (e.length === 0 || t.length === 0)
    return i;
  if (e.length > t.length) {
    const a = e;
    e = t, t = a;
  }
  const o = new Set(t);
  for (let a = 0; a < e.length && o.size > 0; a++) {
    const l = e[a];
    o.delete(l) && i.push(l);
  }
  return i;
}
function Wy(e) {
  return e.length === 0;
}
function rf(e) {
  return (t, i) => {
    const o = t.length - i.length;
    if (o !== 0)
      return o;
    for (let a = 0; a < t.length; a++)
      if (t[a] !== i[a]) {
        const l = e(t[a], i[a]);
        if (l !== 0)
          return l;
      }
    return 0;
  };
}
function t0(e, { threshold: t = 12 } = {}) {
  return (i) => {
    const o = i.length;
    if (o === 0)
      return i;
    if (o <= t) {
      const c = [];
      let f = 0;
      e: for (let d = 0; d < o; d++) {
        const m = i[d];
        for (let y = 0; y < f; y++)
          if (e(m, c[y]) === 0)
            continue e;
        f = c.push(m);
      }
      return c;
    }
    const a = i.slice().sort(e);
    let l = 0;
    for (let c = 1; c < o; c++)
      e(a[l], a[c]) !== 0 && ++l !== c && (a[l] = a[c]);
    return a.length = l + 1, a;
  };
}
function $P(e) {
  return (t, i) => {
    const o = [];
    let a = t.length, l = i.length;
    if (a === 0 || l === 0)
      return o;
    if (a > l) {
      const y = t;
      t = i, i = y;
      const h = a;
      a = l, l = h;
    }
    const c = [...t].sort(e), f = [...i].sort(e);
    let d = 0, m = 0;
    for (; d < a && m < l; ) {
      const y = e(c[d], f[m]);
      y === 0 ? ((o.length === 0 || e(o[o.length - 1], c[d]) !== 0) && o.push(c[d]), d++, m++) : y < 0 ? d++ : m++;
    }
    return o;
  };
}
function OP(e, t) {
  return (i) => {
    if (e.has(i))
      return e.get(i);
    const o = t(i);
    return e.set(i, o), o;
  };
}
const Hy = OP, n0 = () => 0, PP = (e) => e === void 0, CP = (e) => typeof e != "object", qy = {
  boolean: 0,
  number: 1,
  string: 2
};
function kP(e, t) {
  const i = typeof e, o = typeof t;
  return i === o ? so(e, t) : qy[i] - qy[o];
}
function TP(e, t) {
  const i = e.length;
  if (i === 0)
    return t;
  const o = t.length;
  if (o === 0)
    return e;
  if (o > i) {
    const c = e;
    e = t, t = c;
  }
  const a = new Set(e), l = t.length;
  for (let c = 0; c < l; c++) {
    const f = t[c];
    a.has(f) || e.push(f);
  }
  return e;
}
function Jl(e, t, i = n0) {
  return (o, a) => e(o) ? e(a) ? i(o, a) : -1 : e(a) ? 1 : t(o, a);
}
function io(e) {
  return Jl(PP, e);
}
function jr(e, t) {
  return Jl((i) => i === void 0 || e(i), t);
}
function of(e, t) {
  return Jl(Array.isArray, e, t);
}
const ft = io(so), sf = jr((e) => e === 0, (e, t) => e - t);
function NP({ deduplicationCache: e = /* @__PURE__ */ new WeakMap(), sortedKeysCache: t = /* @__PURE__ */ new WeakMap() } = {}) {
  const i = Hy(t, (w) => Object.keys(w).sort());
  function o(w) {
    return (_, E) => {
      const k = i(_), j = i(E), T = Math.min(k.length, j.length);
      for (let N = 0; N < T; N++) {
        const x = so(k[N], j[N]);
        if (x !== 0)
          return x;
      }
      if (k.length !== j.length)
        return k.length - j.length;
      for (let N = 0; N < T; N++) {
        const x = k[N], F = w(_[x], E[x]);
        if (F !== 0)
          return F;
      }
      return 0;
    };
  }
  function a(w) {
    const _ = rf(w), E = Hy(
      e,
      // NOTE: Always sort output
      t0(w, { threshold: 0 })
    );
    return (k, j) => _(E(k), E(j));
  }
  const l = a(so);
  function c(w, _) {
    if (Sl(w)) {
      if (Sl(_)) {
        const E = Object.keys(w), k = Object.keys(_), j = TP(E, k), T = j.length;
        for (let N = 0; N < T; N++) {
          const x = j[N];
          if (w[x] === _[x])
            continue;
          const V = (v[x] ?? f)(w[x], _[x]);
          if (V !== 0)
            return V;
        }
        return 0;
      }
      return _ === !0 && gs(w) ? 0 : 1;
    }
    return Sl(_) ? w === !0 && gs(_) ? 0 : -1 : so(w, _);
  }
  const f = io(m), d = Jl(CP, of(o(f), rf(m)), kP);
  function m(w, _) {
    return w === null ? -1 : _ === null ? 1 : d(w, _);
  }
  const y = io(c), h = jr(gs, o(y)), S = io(a(c)), $ = jr(An, c), v = {
    $id: ft,
    $comment: ft,
    $defs: h,
    $ref: ft,
    $schema: ft,
    const: f,
    contains: y,
    contentEncoding: ft,
    contentMediaType: ft,
    default: f,
    definitions: h,
    description: ft,
    else: y,
    examples: f,
    exclusiveMaximum: ft,
    exclusiveMinimum: ft,
    format: ft,
    if: y,
    maximum: ft,
    maxItems: ft,
    maxLength: ft,
    maxProperties: ft,
    minimum: ft,
    multipleOf: ft,
    not: y,
    pattern: ft,
    propertyNames: y,
    readOnly: ft,
    then: y,
    title: ft,
    writeOnly: ft,
    uniqueItems: jr((w) => w === !1, n0),
    minLength: sf,
    minItems: sf,
    minProperties: sf,
    required: jr(Wy, l),
    enum: jr(Wy, a(m)),
    type: io((w, _) => {
      const E = Array.isArray(w), k = Array.isArray(_);
      return !E && !k ? so(w, _) : l(E ? w : [w], k ? _ : [_]);
    }),
    items: jr((w) => !Array.isArray(w) && An(w), of(c, rf(c))),
    anyOf: S,
    allOf: S,
    oneOf: S,
    properties: h,
    patternProperties: h,
    additionalProperties: $,
    additionalItems: $,
    dependencies: jr(gs, o(io(of(c, l))))
  };
  return {
    compareSchemaValues: m,
    compareSchemaDefinitions: c
  };
}
function Gy(e) {
  return e;
}
const r0 = (e, t) => e ? r0(t % e, e) : t, IP = (e, t) => Math.abs(e * t) / r0(e, t);
function jP(e, t) {
  return e === t ? e : `^(?=.*(?:${e}))(?=.*(?:${t})).*$`;
}
function* af(e, t, i) {
  const o = e.length, a = t.length;
  if (o > 0 && a > 0)
    for (let l = 0; l < o; l++) {
      const c = e[l];
      for (let f = 0; f < a; f++)
        yield i(c, t[f]);
    }
}
function lf(e, t) {
  return e || t;
}
function Yy(e) {
  return (t, i) => {
    const o = { ...t }, a = Object.keys(i), l = a.length;
    for (let c = 0; c < l; c++) {
      const f = a[c];
      o[f] = t[f] === void 0 ? i[f] : e(t[f], i[f]);
    }
    return o;
  };
}
function AP(e) {
  const t = /* @__PURE__ */ new Map();
  for (const i of e)
    for (const o of i[0])
      t.set(o, i[1]);
  return t;
}
function si(e, t, i) {
  i === void 0 || An(i) ? delete e[t] : e[t] = i;
}
const xP = [
  "properties",
  "patternProperties",
  "additionalProperties"
];
function Qy(e) {
  const t = Object.keys(e), i = t.length, o = [];
  for (let a = 0; a < i; a++) {
    const l = t[a];
    o.push({
      regExp: new RegExp(l),
      schema: e[l]
    });
  }
  return [o, t];
}
const Jy = [[], []];
function Xy(e, t, i) {
  const o = i.length;
  for (let a = 0; a < o; a++) {
    const l = i[a];
    if (!l.regExp.test(t))
      continue;
    const c = l.schema;
    if (c === !1)
      return !0;
    e.push(c);
  }
  return !1;
}
const bP = [
  "items",
  "additionalItems"
], FP = [
  "if",
  "then",
  "else"
];
function Zy(e, t) {
  return t.if !== void 0 && (e.if = t.if), t.then !== void 0 && (e.then = t.then), t.else !== void 0 && (e.else = t.else), e;
}
function uf(e, t) {
  if (e === t)
    return e;
  switch (e) {
    case "number":
      if (t === "integer")
        return "integer";
    case "integer":
      if (t === "number")
        return "integer";
    default:
      return;
  }
}
function ai(e, t, i) {
  return [e, t, i];
}
function RP(e) {
  const t = /* @__PURE__ */ new Map();
  for (const [i, o, a] of e) {
    const l = (c) => {
      if (!a(c))
        throw new Error(`Schema keys '${i}' and '${o}' are conflicting (${i}: ${JSON.stringify(c[i])}, ${o}: ${JSON.stringify(c[o])})`);
    };
    for (const c of [
      [i, o],
      [o, i]
    ]) {
      let f = t.get(c[0]);
      f === void 0 && (f = [], t.set(c[0], f)), f.push({ oppositeKey: c[1], check: l });
    }
  }
  return t;
}
const DP = [
  ai("minimum", "maximum", (e) => e.maximum >= e.minimum),
  ai("exclusiveMinimum", "maximum", (e) => e.maximum > e.exclusiveMinimum),
  ai("minimum", "exclusiveMaximum", (e) => e.exclusiveMaximum > e.minimum),
  ai("exclusiveMinimum", "exclusiveMaximum", (e) => e.exclusiveMaximum > e.exclusiveMinimum),
  ai("minLength", "maxLength", (e) => e.maxLength >= e.minLength),
  ai("minItems", "maxItems", (e) => e.maxItems >= e.minItems),
  ai("minProperties", "maxProperties", (e) => e.maxProperties >= e.minProperties)
];
function MP({ mergePatterns: e = jP, isSubRegExp: t = Object.is, intersectJson: i = EP, deduplicateJsonSchemaDef: o = Gy, defaultMerger: a = Gy, assigners: l = [], checks: c = DP, mergers: f } = {}) {
  function d(T) {
    const N = T.length;
    let x = T[0];
    for (let F = 1; F < N; F++) {
      const V = E(x, T[F]);
      if (V === !1)
        return !1;
      An(V) || (x = V);
    }
    return x;
  }
  function m(T, N, x, F, V, U, G) {
    if (T.length = 0, x === !1)
      return !1;
    if (T.push(x), V !== void 0) {
      if (V === !1)
        return !1;
      T.push(V);
    }
    if (Xy(T, N, U))
      return !1;
    const H = T.length < 2;
    if (G === !1) {
      if (H)
        return;
      if (Xy(T, N, F))
        return !1;
    } else H && G !== void 0 && T.push(G);
    return T.length === 1 ? T[0] : d(T);
  }
  function y(T, N, x, F, V, U) {
    const G = x.length;
    if (G > 0 && V !== !1)
      if (U)
        Object.assign(T, N);
      else
        for (let Q = 0; Q < G; Q++) {
          const H = x[Q];
          F.has(H) || (T[H] = E(N[H], V));
        }
    return T;
  }
  const h = (T, { properties: N = {}, patternProperties: x, additionalProperties: F = !0 }, { properties: V = {}, patternProperties: U, additionalProperties: G = !0 }) => {
    const Q = An(F), H = An(G);
    if (Q && H)
      return si(T, "properties", k(N, V)), si(T, "patternProperties", x && U ? k(x, U) : x ?? U), delete T.additionalProperties, T;
    const q = E(F, G);
    si(T, "additionalProperties", q);
    const le = {}, ie = Object.keys(N), ne = ie.length, [pe, Z] = x ? Qy(x) : Jy, [ae, z] = U ? Qy(U) : Jy, P = [], b = /* @__PURE__ */ new Set(), R = H ? void 0 : G;
    for (let se = 0; se < ne; se++) {
      const ce = ie[se];
      b.add(ce);
      const $e = m(P, ce, N[ce], pe, V[ce], ae, R);
      $e !== void 0 && (le[ce] = $e);
    }
    const C = Object.keys(V), I = C.length, B = Q ? void 0 : F;
    for (let se = 0; se < I; se++) {
      const ce = C[se];
      if (b.has(ce))
        continue;
      const $e = m(P, ce, V[ce], ae, void 0, pe, B);
      $e !== void 0 && (le[ce] = $e);
    }
    si(T, "properties", le);
    let X = {};
    const J = /* @__PURE__ */ new Set();
    if (Z.length > 0 && z.length > 0) {
      const se = af(Z, z, (ce, $e) => {
        t(ce, $e) && J.add(ce), t($e, ce) && J.add($e), X[e(ce, $e)] = E(x[ce], U[$e]);
      });
      for (; !se.next().done; )
        ;
    }
    return X = y(X, x, Z, J, G, H), X = y(X, U, z, J, F, Q), si(T, "patternProperties", X), T;
  }, S = (T, { items: N = [], additionalItems: x }, { items: F = [], additionalItems: V }) => {
    const U = Array.isArray(N), G = Array.isArray(F), Q = [];
    if (T.items = Q, U && G) {
      const [H, q, le] = N.length < F.length ? [N.length, x, F] : [F.length, V, N];
      let ie = 0;
      for (; ie < H; ie++)
        Q.push(E(N[ie], F[ie]));
      if (q === !1)
        T.additionalItems = !1;
      else {
        const ne = q === void 0 || An(q);
        for (; ie < le.length; ie++)
          Q.push(ne ? le[ie] : E(le[ie], q));
        si(T, "additionalItems", x !== void 0 && V !== void 0 ? E(x, V) : x ?? V);
      }
    } else if (U || G) {
      const [H, q, le] = U ? [N, F, x] : [F, N, V];
      si(T, "additionalItems", le && E(le, q));
      for (let ie = 0; ie < H.length; ie++)
        Q.push(E(H[ie], q));
    } else
      delete T.additionalItems, T.items = E(N, F);
    return T;
  }, $ = (T, N, x) => {
    Zy(T, N);
    const F = Zy({}, x);
    return T.allOf === void 0 ? T.allOf = [F] : T.allOf = T.allOf.concat(F), T;
  };
  function v(T, N) {
    return o(Array.from(af(T, N, E)));
  }
  const w = AP([
    [xP, h],
    [bP, S],
    [FP, $],
    ...l
  ]), _ = RP(c);
  function E(T, N) {
    if (T === !1 || N === !1)
      return !1;
    if (An(T))
      return An(N) ? !0 : N;
    if (An(N))
      return T;
    let x = { ...T };
    const F = /* @__PURE__ */ new Set(), V = /* @__PURE__ */ new Set(), U = Object.keys(N), G = U.length;
    for (let Q = 0; Q < G; Q++) {
      const H = U[Q], q = N[H];
      if (q === void 0)
        continue;
      const le = _.get(H);
      if (le !== void 0) {
        const Z = le.length;
        for (let ae = 0; ae < Z; ae++) {
          const z = le[ae];
          T[z.oppositeKey] !== void 0 && V.add(z.check);
        }
      }
      const ie = T[H];
      if (ie === void 0) {
        x[H] = q;
        continue;
      }
      const ne = w.get(H);
      if (ne) {
        F.add(ne);
        continue;
      }
      const pe = j[H] ?? a;
      x[H] = pe(ie, q);
    }
    for (const Q of F)
      x = Q(x, T, N);
    for (const Q of V)
      Q(x);
    return x;
  }
  const k = Yy(E), j = {
    $id: a,
    $ref: a,
    $schema: a,
    $comment: a,
    $defs: k,
    definitions: k,
    type: (T, N) => {
      if (T === N)
        return T;
      const x = Array.isArray(T), F = Array.isArray(N);
      if (!x && !F) {
        const V = uf(T, N);
        if (V !== void 0)
          return V;
      } else if (x || F) {
        const V = /* @__PURE__ */ new Set();
        if (x && F)
          for (const G of af(T, N, uf))
            G !== void 0 && V.add(G);
        else {
          const G = x ? T : N, Q = x ? N : T, H = G.length;
          for (let q = 0; q < H; q++) {
            const le = uf(Q, G[q]);
            le !== void 0 && V.add(le);
          }
        }
        const U = V.size;
        if (U === 1)
          return V.values().next().value;
        if (U > 1)
          return Array.from(V);
      }
      throw new Error(`It is not possible to create an intersection of the following incompatible types: ${T.toString()}, ${N.toString()}`);
    },
    default: a,
    description: a,
    title: a,
    const: a,
    format: a,
    contentEncoding: a,
    contentMediaType: a,
    not: (T, N) => {
      const x = o([T, N]);
      return x.length === 1 ? x[0] : { anyOf: x };
    },
    pattern: e,
    readOnly: lf,
    writeOnly: lf,
    enum: (T, N) => {
      const x = i(T, N);
      if (x.length === 0)
        throw new Error(`Intersection of the following enums is empty: "${JSON.stringify(T)}", "${JSON.stringify(N)}"`);
      return x;
    },
    anyOf: v,
    oneOf: v,
    allOf: (T, N) => o(T.concat(N)),
    propertyNames: E,
    contains: E,
    dependencies: Yy((T, N) => Array.isArray(T) ? Array.isArray(N) ? nf(T, N) : E(N, { required: T }) : Array.isArray(N) ? E(T, { required: N }) : E(T, N)),
    examples: (T, N) => {
      if (!Array.isArray(T) || !Array.isArray(N))
        throw new Error(`Value of the 'examples' field should be an array, but got "${JSON.stringify(T)}" and "${JSON.stringify(N)}"`);
      return nf(T, N);
    },
    multipleOf: (T, N) => {
      let x = 1;
      for (; !Number.isInteger(T) || !Number.isInteger(N); )
        x *= 10, T *= 10, N *= 10;
      return IP(T, N) / x;
    },
    exclusiveMaximum: Math.min,
    maximum: Math.min,
    maxItems: Math.min,
    maxLength: Math.min,
    maxProperties: Math.min,
    exclusiveMinimum: Math.max,
    minimum: Math.max,
    minItems: Math.max,
    minLength: Math.max,
    minProperties: Math.max,
    uniqueItems: lf,
    required: nf,
    ...f
  };
  return {
    mergeSchemaDefinitions: E,
    mergeArrayOfSchemaDefinitions: d
  };
}
function LP(e) {
  const t = [], i = [e];
  for (; i.length > 0; ) {
    const o = i.pop();
    if (typeof o == "boolean" || o.allOf === void 0) {
      t.push(o);
      continue;
    }
    const { allOf: a, ...l } = o;
    t.push(l);
    for (let c = a.length - 1; c >= 0; c--)
      i.push(a[c]);
  }
  return t;
}
function UP(e) {
  return (t) => e(LP(t));
}
var lo = {}, zP = /~/, VP = /~[01]/g;
function BP(e) {
  switch (e) {
    case "~1":
      return "/";
    case "~0":
      return "~";
  }
  throw new Error("Invalid tilde escape: " + e);
}
function i0(e) {
  return zP.test(e) ? e.replace(VP, BP) : e;
}
function KP(e, t, i) {
  for (var o, a, l = 1, c = t.length; l < c; ) {
    if (t[l] === "constructor" || t[l] === "prototype" || t[l] === "__proto__") return e;
    if (o = i0(t[l++]), a = c > l, typeof e[o] > "u" && (Array.isArray(e) && o === "-" && (o = e.length), a && (t[l] !== "" && t[l] < 1 / 0 || t[l] === "-" ? e[o] = [] : e[o] = {})), !a) break;
    e = e[o];
  }
  var f = e[o];
  return i === void 0 ? delete e[o] : e[o] = i, f;
}
function yd(e) {
  if (typeof e == "string") {
    if (e = e.split("/"), e[0] === "") return e;
    throw new Error("Invalid JSON pointer.");
  } else if (Array.isArray(e)) {
    for (const t of e)
      if (typeof t != "string" && typeof t != "number")
        throw new Error("Invalid JSON pointer. Must be of type string or number.");
    return e;
  }
  throw new Error("Invalid JSON pointer.");
}
function o0(e, t) {
  if (typeof e != "object") throw new Error("Invalid input object.");
  t = yd(t);
  var i = t.length;
  if (i === 1) return e;
  for (var o = 1; o < i; ) {
    if (e = e[i0(t[o++])], i === o) return e;
    if (typeof e != "object" || e === null) return;
  }
}
function s0(e, t, i) {
  if (typeof e != "object") throw new Error("Invalid input object.");
  if (t = yd(t), t.length === 0) throw new Error("Invalid JSON pointer for set.");
  return KP(e, t, i);
}
function WP(e) {
  var t = yd(e);
  return {
    get: function(i) {
      return o0(i, t);
    },
    set: function(i, o) {
      return s0(i, t, o);
    }
  };
}
lo.get = o0;
lo.set = s0;
lo.compile = WP;
function HP(e, t) {
  return e && Eo(t, vn(t), e);
}
function qP(e, t) {
  return e && Eo(t, qs(t), e);
}
function GP(e, t) {
  return Eo(e, nd(e), t);
}
var YP = Object.getOwnPropertySymbols, a0 = YP ? function(e) {
  for (var t = []; e; )
    td(t, nd(e)), e = Bl(e);
  return t;
} : Cv;
function QP(e, t) {
  return Eo(e, a0(e), t);
}
function gd(e) {
  return Pv(e, qs, a0);
}
var JP = Object.prototype, XP = JP.hasOwnProperty;
function ZP(e) {
  var t = e.length, i = new e.constructor(t);
  return t && typeof e[0] == "string" && XP.call(e, "index") && (i.index = e.index, i.input = e.input), i;
}
function eC(e, t) {
  var i = t ? pd(e.buffer) : e.buffer;
  return new e.constructor(i, e.byteOffset, e.byteLength);
}
var tC = /\w*$/;
function nC(e) {
  var t = new e.constructor(e.source, tC.exec(e));
  return t.lastIndex = e.lastIndex, t;
}
var eg = sn ? sn.prototype : void 0, tg = eg ? eg.valueOf : void 0;
function rC(e) {
  return tg ? Object(tg.call(e)) : {};
}
var iC = "[object Boolean]", oC = "[object Date]", sC = "[object Map]", aC = "[object Number]", lC = "[object RegExp]", uC = "[object Set]", cC = "[object String]", fC = "[object Symbol]", dC = "[object ArrayBuffer]", pC = "[object DataView]", hC = "[object Float32Array]", mC = "[object Float64Array]", yC = "[object Int8Array]", gC = "[object Int16Array]", vC = "[object Int32Array]", _C = "[object Uint8Array]", SC = "[object Uint8ClampedArray]", wC = "[object Uint16Array]", EC = "[object Uint32Array]";
function $C(e, t, i) {
  var o = e.constructor;
  switch (t) {
    case dC:
      return pd(e);
    case iC:
    case oC:
      return new o(+e);
    case pC:
      return eC(e, i);
    case hC:
    case mC:
    case yC:
    case gC:
    case vC:
    case _C:
    case SC:
    case wC:
    case EC:
      return qv(e, i);
    case sC:
      return new o();
    case aC:
    case cC:
      return new o(e);
    case lC:
      return nC(e);
    case uC:
      return new o();
    case fC:
      return rC(e);
  }
}
var OC = "[object Map]";
function PC(e) {
  return an(e) && rn(e) == OC;
}
var ng = mo && mo.isMap, CC = ng ? id(ng) : PC, kC = "[object Set]";
function TC(e) {
  return an(e) && rn(e) == kC;
}
var rg = mo && mo.isSet, NC = rg ? id(rg) : TC, IC = 1, jC = 2, AC = 4, l0 = "[object Arguments]", xC = "[object Array]", bC = "[object Boolean]", FC = "[object Date]", RC = "[object Error]", u0 = "[object Function]", DC = "[object GeneratorFunction]", MC = "[object Map]", LC = "[object Number]", c0 = "[object Object]", UC = "[object RegExp]", zC = "[object Set]", VC = "[object String]", BC = "[object Symbol]", KC = "[object WeakMap]", WC = "[object ArrayBuffer]", HC = "[object DataView]", qC = "[object Float32Array]", GC = "[object Float64Array]", YC = "[object Int8Array]", QC = "[object Int16Array]", JC = "[object Int32Array]", XC = "[object Uint8Array]", ZC = "[object Uint8ClampedArray]", ek = "[object Uint16Array]", tk = "[object Uint32Array]", qe = {};
qe[l0] = qe[xC] = qe[WC] = qe[HC] = qe[bC] = qe[FC] = qe[qC] = qe[GC] = qe[YC] = qe[QC] = qe[JC] = qe[MC] = qe[LC] = qe[c0] = qe[UC] = qe[zC] = qe[VC] = qe[BC] = qe[XC] = qe[ZC] = qe[ek] = qe[tk] = !0;
qe[RC] = qe[u0] = qe[KC] = !1;
function Es(e, t, i, o, a, l) {
  var c, f = t & IC, d = t & jC, m = t & AC;
  if (i && (c = a ? i(e, o, a, l) : i(e)), c !== void 0)
    return c;
  if (!Fe(e))
    return e;
  var y = yt(e);
  if (y) {
    if (c = ZP(e), !f)
      return hd(e, c);
  } else {
    var h = rn(e), S = h == u0 || h == DC;
    if (yi(e))
      return Hv(e, f);
    if (h == c0 || h == l0 || S && !a) {
      if (c = d || S ? {} : Gv(e), !f)
        return d ? QP(e, qP(c, e)) : GP(e, HP(c, e));
    } else {
      if (!qe[h])
        return a ? e : {};
      c = $C(e, h, f);
    }
  }
  l || (l = new Sn());
  var $ = l.get(e);
  if ($)
    return $;
  l.set(e, c), NC(e) ? e.forEach(function(_) {
    c.add(Es(_, t, i, _, e, l));
  }) : CC(e) && e.forEach(function(_, E) {
    c.set(E, Es(_, t, i, E, e, l));
  });
  var v = m ? d ? gd : Tf : d ? qs : vn, w = y ? void 0 : v(e);
  return fd(w || e, function(_, E) {
    w && (E = _, _ = e[E]), ud(c, E, Es(_, t, i, E, e, l));
  }), c;
}
function f0(e) {
  var t = e == null ? 0 : e.length;
  return t ? e[t - 1] : void 0;
}
function nk(e, t, i) {
  var o = -1, a = e.length;
  t < 0 && (t = -t > a ? 0 : a + t), i = i > a ? a : i, i < 0 && (i += a), a = t > i ? 0 : i - t >>> 0, t >>>= 0;
  for (var l = Array(a); ++o < a; )
    l[o] = e[o + t];
  return l;
}
function rk(e, t) {
  return t.length < 2 ? e : Gl(e, nk(t, 0, -1));
}
function d0(e, t) {
  return t = wo(t, e), e = rk(e, t), e == null || delete e[$i(f0(t))];
}
function ik(e) {
  return zr(e) ? void 0 : e;
}
function bf(e) {
  var t = e == null ? 0 : e.length;
  return t ? Gs(e, 1) : [];
}
function p0(e) {
  return Jv(Qv(e, void 0, bf), e + "");
}
var ok = 1, sk = 2, ak = 4, Fs = p0(function(e, t) {
  var i = {};
  if (e == null)
    return i;
  var o = !1;
  t = So(t, function(l) {
    return l = wo(l, e), o || (o = l.length > 1), l;
  }), Eo(e, gd(e), i), o && (i = Es(i, ok | sk | ak, ik));
  for (var a = t.length; a--; )
    d0(i, t[a]);
  return i;
}), Xl = { exports: {} };
const lk = RegExp.prototype.test.bind(/^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/iu), h0 = RegExp.prototype.test.bind(/^(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|\d)$/u);
function m0(e) {
  let t = "", i = 0, o = 0;
  for (o = 0; o < e.length; o++)
    if (i = e[o].charCodeAt(0), i !== 48) {
      if (!(i >= 48 && i <= 57 || i >= 65 && i <= 70 || i >= 97 && i <= 102))
        return "";
      t += e[o];
      break;
    }
  for (o += 1; o < e.length; o++) {
    if (i = e[o].charCodeAt(0), !(i >= 48 && i <= 57 || i >= 65 && i <= 70 || i >= 97 && i <= 102))
      return "";
    t += e[o];
  }
  return t;
}
const uk = RegExp.prototype.test.bind(/[^!"$&'()*+,\-.;=_`a-z{}~]/u);
function ig(e) {
  return e.length = 0, !0;
}
function ck(e, t, i) {
  if (e.length) {
    const o = m0(e);
    if (o !== "")
      t.push(o);
    else
      return i.error = !0, !1;
    e.length = 0;
  }
  return !0;
}
function fk(e) {
  let t = 0;
  const i = { error: !1, address: "", zone: "" }, o = [], a = [];
  let l = !1, c = !1, f = ck;
  for (let d = 0; d < e.length; d++) {
    const m = e[d];
    if (!(m === "[" || m === "]"))
      if (m === ":") {
        if (l === !0 && (c = !0), !f(a, o, i))
          break;
        if (++t > 7) {
          i.error = !0;
          break;
        }
        d > 0 && e[d - 1] === ":" && (l = !0), o.push(":");
        continue;
      } else if (m === "%") {
        if (!f(a, o, i))
          break;
        f = ig;
      } else {
        a.push(m);
        continue;
      }
  }
  return a.length && (f === ig ? i.zone = a.join("") : c ? o.push(a.join("")) : o.push(m0(a))), i.address = o.join(""), i;
}
function y0(e) {
  if (dk(e, ":") < 2)
    return { host: e, isIPV6: !1 };
  const t = fk(e);
  if (t.error)
    return { host: e, isIPV6: !1 };
  {
    let i = t.address, o = t.address;
    return t.zone && (i += "%" + t.zone, o += "%25" + t.zone), { host: i, isIPV6: !0, escapedHost: o };
  }
}
function dk(e, t) {
  let i = 0;
  for (let o = 0; o < e.length; o++)
    e[o] === t && i++;
  return i;
}
function pk(e) {
  let t = e;
  const i = [];
  let o = -1, a = 0;
  for (; a = t.length; ) {
    if (a === 1) {
      if (t === ".")
        break;
      if (t === "/") {
        i.push("/");
        break;
      } else {
        i.push(t);
        break;
      }
    } else if (a === 2) {
      if (t[0] === ".") {
        if (t[1] === ".")
          break;
        if (t[1] === "/") {
          t = t.slice(2);
          continue;
        }
      } else if (t[0] === "/" && (t[1] === "." || t[1] === "/")) {
        i.push("/");
        break;
      }
    } else if (a === 3 && t === "/..") {
      i.length !== 0 && i.pop(), i.push("/");
      break;
    }
    if (t[0] === ".") {
      if (t[1] === ".") {
        if (t[2] === "/") {
          t = t.slice(3);
          continue;
        }
      } else if (t[1] === "/") {
        t = t.slice(2);
        continue;
      }
    } else if (t[0] === "/" && t[1] === ".") {
      if (t[2] === "/") {
        t = t.slice(2);
        continue;
      } else if (t[2] === "." && t[3] === "/") {
        t = t.slice(3), i.length !== 0 && i.pop();
        continue;
      }
    }
    if ((o = t.indexOf("/", 1)) === -1) {
      i.push(t);
      break;
    } else
      i.push(t.slice(0, o)), t = t.slice(o);
  }
  return i.join("");
}
function hk(e, t) {
  const i = t !== !0 ? escape : unescape;
  return e.scheme !== void 0 && (e.scheme = i(e.scheme)), e.userinfo !== void 0 && (e.userinfo = i(e.userinfo)), e.host !== void 0 && (e.host = i(e.host)), e.path !== void 0 && (e.path = i(e.path)), e.query !== void 0 && (e.query = i(e.query)), e.fragment !== void 0 && (e.fragment = i(e.fragment)), e;
}
function mk(e) {
  const t = [];
  if (e.userinfo !== void 0 && (t.push(e.userinfo), t.push("@")), e.host !== void 0) {
    let i = unescape(e.host);
    if (!h0(i)) {
      const o = y0(i);
      o.isIPV6 === !0 ? i = `[${o.escapedHost}]` : i = e.host;
    }
    t.push(i);
  }
  return (typeof e.port == "number" || typeof e.port == "string") && (t.push(":"), t.push(String(e.port))), t.length ? t.join("") : void 0;
}
var g0 = {
  nonSimpleDomain: uk,
  recomposeAuthority: mk,
  normalizeComponentEncoding: hk,
  removeDotSegments: pk,
  isIPv4: h0,
  isUUID: lk,
  normalizeIPv6: y0
};
const { isUUID: yk } = g0, gk = /([\da-z][\d\-a-z]{0,31}):((?:[\w!$'()*+,\-.:;=@]|%[\da-f]{2})+)/iu;
function v0(e) {
  return e.secure === !0 ? !0 : e.secure === !1 ? !1 : e.scheme ? e.scheme.length === 3 && (e.scheme[0] === "w" || e.scheme[0] === "W") && (e.scheme[1] === "s" || e.scheme[1] === "S") && (e.scheme[2] === "s" || e.scheme[2] === "S") : !1;
}
function _0(e) {
  return e.host || (e.error = e.error || "HTTP URIs must have a host."), e;
}
function S0(e) {
  const t = String(e.scheme).toLowerCase() === "https";
  return (e.port === (t ? 443 : 80) || e.port === "") && (e.port = void 0), e.path || (e.path = "/"), e;
}
function vk(e) {
  return e.secure = v0(e), e.resourceName = (e.path || "/") + (e.query ? "?" + e.query : ""), e.path = void 0, e.query = void 0, e;
}
function _k(e) {
  if ((e.port === (v0(e) ? 443 : 80) || e.port === "") && (e.port = void 0), typeof e.secure == "boolean" && (e.scheme = e.secure ? "wss" : "ws", e.secure = void 0), e.resourceName) {
    const [t, i] = e.resourceName.split("?");
    e.path = t && t !== "/" ? t : void 0, e.query = i, e.resourceName = void 0;
  }
  return e.fragment = void 0, e;
}
function Sk(e, t) {
  if (!e.path)
    return e.error = "URN can not be parsed", e;
  const i = e.path.match(gk);
  if (i) {
    const o = t.scheme || e.scheme || "urn";
    e.nid = i[1].toLowerCase(), e.nss = i[2];
    const a = `${o}:${t.nid || e.nid}`, l = vd(a);
    e.path = void 0, l && (e = l.parse(e, t));
  } else
    e.error = e.error || "URN can not be parsed.";
  return e;
}
function wk(e, t) {
  if (e.nid === void 0)
    throw new Error("URN without nid cannot be serialized");
  const i = t.scheme || e.scheme || "urn", o = e.nid.toLowerCase(), a = `${i}:${t.nid || o}`, l = vd(a);
  l && (e = l.serialize(e, t));
  const c = e, f = e.nss;
  return c.path = `${o || t.nid}:${f}`, t.skipEscape = !0, c;
}
function Ek(e, t) {
  const i = e;
  return i.uuid = i.nss, i.nss = void 0, !t.tolerant && (!i.uuid || !yk(i.uuid)) && (i.error = i.error || "UUID is not valid."), i;
}
function $k(e) {
  const t = e;
  return t.nss = (e.uuid || "").toLowerCase(), t;
}
const w0 = (
  /** @type {SchemeHandler} */
  {
    scheme: "http",
    domainHost: !0,
    parse: _0,
    serialize: S0
  }
), Ok = (
  /** @type {SchemeHandler} */
  {
    scheme: "https",
    domainHost: w0.domainHost,
    parse: _0,
    serialize: S0
  }
), wl = (
  /** @type {SchemeHandler} */
  {
    scheme: "ws",
    domainHost: !0,
    parse: vk,
    serialize: _k
  }
), Pk = (
  /** @type {SchemeHandler} */
  {
    scheme: "wss",
    domainHost: wl.domainHost,
    parse: wl.parse,
    serialize: wl.serialize
  }
), Ck = (
  /** @type {SchemeHandler} */
  {
    scheme: "urn",
    parse: Sk,
    serialize: wk,
    skipNormalize: !0
  }
), kk = (
  /** @type {SchemeHandler} */
  {
    scheme: "urn:uuid",
    parse: Ek,
    serialize: $k,
    skipNormalize: !0
  }
), bl = (
  /** @type {Record<SchemeName, SchemeHandler>} */
  {
    http: w0,
    https: Ok,
    ws: wl,
    wss: Pk,
    urn: Ck,
    "urn:uuid": kk
  }
);
Object.setPrototypeOf(bl, null);
function vd(e) {
  return e && (bl[
    /** @type {SchemeName} */
    e
  ] || bl[
    /** @type {SchemeName} */
    e.toLowerCase()
  ]) || void 0;
}
var Tk = {
  SCHEMES: bl,
  getSchemeHandler: vd
};
const { normalizeIPv6: Nk, removeDotSegments: vs, recomposeAuthority: Ik, normalizeComponentEncoding: ll, isIPv4: jk, nonSimpleDomain: Ak } = g0, { SCHEMES: xk, getSchemeHandler: E0 } = Tk;
function bk(e, t) {
  return typeof e == "string" ? e = /** @type {T} */
  Fn(rr(e, t), t) : typeof e == "object" && (e = /** @type {T} */
  rr(Fn(e, t), t)), e;
}
function Fk(e, t, i) {
  const o = i ? Object.assign({ scheme: "null" }, i) : { scheme: "null" }, a = $0(rr(e, o), rr(t, o), o, !0);
  return o.skipEscape = !0, Fn(a, o);
}
function $0(e, t, i, o) {
  const a = {};
  return o || (e = rr(Fn(e, i), i), t = rr(Fn(t, i), i)), i = i || {}, !i.tolerant && t.scheme ? (a.scheme = t.scheme, a.userinfo = t.userinfo, a.host = t.host, a.port = t.port, a.path = vs(t.path || ""), a.query = t.query) : (t.userinfo !== void 0 || t.host !== void 0 || t.port !== void 0 ? (a.userinfo = t.userinfo, a.host = t.host, a.port = t.port, a.path = vs(t.path || ""), a.query = t.query) : (t.path ? (t.path[0] === "/" ? a.path = vs(t.path) : ((e.userinfo !== void 0 || e.host !== void 0 || e.port !== void 0) && !e.path ? a.path = "/" + t.path : e.path ? a.path = e.path.slice(0, e.path.lastIndexOf("/") + 1) + t.path : a.path = t.path, a.path = vs(a.path)), a.query = t.query) : (a.path = e.path, t.query !== void 0 ? a.query = t.query : a.query = e.query), a.userinfo = e.userinfo, a.host = e.host, a.port = e.port), a.scheme = e.scheme), a.fragment = t.fragment, a;
}
function Rk(e, t, i) {
  return typeof e == "string" ? (e = unescape(e), e = Fn(ll(rr(e, i), !0), { ...i, skipEscape: !0 })) : typeof e == "object" && (e = Fn(ll(e, !0), { ...i, skipEscape: !0 })), typeof t == "string" ? (t = unescape(t), t = Fn(ll(rr(t, i), !0), { ...i, skipEscape: !0 })) : typeof t == "object" && (t = Fn(ll(t, !0), { ...i, skipEscape: !0 })), e.toLowerCase() === t.toLowerCase();
}
function Fn(e, t) {
  const i = {
    host: e.host,
    scheme: e.scheme,
    userinfo: e.userinfo,
    port: e.port,
    path: e.path,
    query: e.query,
    nid: e.nid,
    nss: e.nss,
    uuid: e.uuid,
    fragment: e.fragment,
    reference: e.reference,
    resourceName: e.resourceName,
    secure: e.secure,
    error: ""
  }, o = Object.assign({}, t), a = [], l = E0(o.scheme || i.scheme);
  l && l.serialize && l.serialize(i, o), i.path !== void 0 && (o.skipEscape ? i.path = unescape(i.path) : (i.path = escape(i.path), i.scheme !== void 0 && (i.path = i.path.split("%3A").join(":")))), o.reference !== "suffix" && i.scheme && a.push(i.scheme, ":");
  const c = Ik(i);
  if (c !== void 0 && (o.reference !== "suffix" && a.push("//"), a.push(c), i.path && i.path[0] !== "/" && a.push("/")), i.path !== void 0) {
    let f = i.path;
    !o.absolutePath && (!l || !l.absolutePath) && (f = vs(f)), c === void 0 && f[0] === "/" && f[1] === "/" && (f = "/%2F" + f.slice(2)), a.push(f);
  }
  return i.query !== void 0 && a.push("?", i.query), i.fragment !== void 0 && a.push("#", i.fragment), a.join("");
}
const Dk = /^(?:([^#/:?]+):)?(?:\/\/((?:([^#/?@]*)@)?(\[[^#/?\]]+\]|[^#/:?]*)(?::(\d*))?))?([^#?]*)(?:\?([^#]*))?(?:#((?:.|[\n\r])*))?/u;
function rr(e, t) {
  const i = Object.assign({}, t), o = {
    scheme: void 0,
    userinfo: void 0,
    host: "",
    port: void 0,
    path: "",
    query: void 0,
    fragment: void 0
  };
  let a = !1;
  i.reference === "suffix" && (i.scheme ? e = i.scheme + ":" + e : e = "//" + e);
  const l = e.match(Dk);
  if (l) {
    if (o.scheme = l[1], o.userinfo = l[3], o.host = l[4], o.port = parseInt(l[5], 10), o.path = l[6] || "", o.query = l[7], o.fragment = l[8], isNaN(o.port) && (o.port = l[5]), o.host)
      if (jk(o.host) === !1) {
        const d = Nk(o.host);
        o.host = d.host.toLowerCase(), a = d.isIPV6;
      } else
        a = !0;
    o.scheme === void 0 && o.userinfo === void 0 && o.host === void 0 && o.port === void 0 && o.query === void 0 && !o.path ? o.reference = "same-document" : o.scheme === void 0 ? o.reference = "relative" : o.fragment === void 0 ? o.reference = "absolute" : o.reference = "uri", i.reference && i.reference !== "suffix" && i.reference !== o.reference && (o.error = o.error || "URI is not a " + i.reference + " reference.");
    const c = E0(i.scheme || o.scheme);
    if (!i.unicodeSupport && (!c || !c.unicodeSupport) && o.host && (i.domainHost || c && c.domainHost) && a === !1 && Ak(o.host))
      try {
        o.host = URL.domainToASCII(o.host.toLowerCase());
      } catch (f) {
        o.error = o.error || "Host's domain name can not be converted to ASCII: " + f;
      }
    (!c || c && !c.skipNormalize) && (e.indexOf("%") !== -1 && (o.scheme !== void 0 && (o.scheme = unescape(o.scheme)), o.host !== void 0 && (o.host = unescape(o.host))), o.path && (o.path = escape(unescape(o.path))), o.fragment && (o.fragment = encodeURI(decodeURIComponent(o.fragment)))), c && c.parse && c.parse(o, i);
  } else
    o.error = o.error || "URI can not be parsed.";
  return o;
}
const _d = {
  SCHEMES: xk,
  normalize: bk,
  resolve: Fk,
  resolveComponent: $0,
  equal: Rk,
  serialize: Fn,
  parse: rr
};
Xl.exports = _d;
Xl.exports.default = _d;
Xl.exports.fastUri = _d;
var O0 = Xl.exports;
const Sd = /* @__PURE__ */ zs(O0);
function Fl(e, t) {
  if (Ke in e && Sd.equal(e[Ke], t))
    return e;
  for (const i of Object.values(e))
    if (Array.isArray(i)) {
      for (const o of i)
        if (Fe(o)) {
          const a = Fl(o, t);
          if (a !== void 0)
            return a;
        }
    } else if (Fe(i)) {
      const o = Fl(i, t);
      if (o !== void 0)
        return o;
    }
}
function Ff(e, t) {
  const i = re(e, Ke, t);
  Ze in e && (e = { ...e, [Ze]: Sd.resolve(i, e[Ze]) });
  for (const [o, a] of Object.entries(e))
    Array.isArray(a) ? e = {
      ...e,
      [o]: a.map((l) => Fe(l) ? Ff(l, i) : l)
    } : Fe(a) && (e = { ...e, [o]: Ff(a, i) });
  return e;
}
function wd(e, t) {
  const i = t[e];
  return [Fs(t, [e]), i];
}
function P0(e, t = {}, i = [], o = re(t, [Ke])) {
  const a = e || "";
  let l;
  if (a.startsWith("#")) {
    const f = decodeURIComponent(a.substring(1));
    o === void 0 || Ke in t && t[Ke] === o ? l = lo.get(t, f) : t[ys] === vl && (l = Fl(t, o.replace(/\/$/, "")), l !== void 0 && (l = lo.get(l, f)));
  } else if (t[ys] === vl) {
    const f = o ? Sd.resolve(o, a) : a, [d, ...m] = f.replace(/#\/?$/, "").split("#");
    l = Fl(t, d.replace(/\/$/, "")), l !== void 0 && (o = l[Ke], dt(m) || (l = lo.get(l, decodeURIComponent(m.join("#")))));
  }
  if (l === void 0)
    throw new Error(`Could not find a definition for ${e}.`);
  const c = l[Ze];
  if (c) {
    if (i.includes(c)) {
      if (i.length === 1)
        throw new Error(`Definition for ${e} is a circular reference`);
      const [y, ...h] = i, S = [...h, a, y].join(" -> ");
      throw new Error(`Definition for ${y} contains a circular reference through ${S}`);
    }
    const [f, d] = wd(Ze, l), m = P0(d, t, [...i, a], o);
    return Object.keys(f).length > 0 ? t[ys] === E1 || t[ys] === vl ? { [Ur]: [f, m] } : { ...f, ...m } : m;
  }
  return l;
}
function C0(e, t = {}, i = re(t, [Ke])) {
  return P0(e, t, [], i);
}
var Mk = "[object String]";
function Vr(e) {
  return typeof e == "string" || !yt(e) && an(e) && or(e) == Mk;
}
function zn(e) {
  let t;
  const i = re(e, _1);
  return Vr(i) ? t = i : i !== void 0 && console.warn(`Expecting discriminator to be a string, got "${typeof i}" instead`), t;
}
function Rs(e) {
  return Array.isArray(e) ? "array" : typeof e == "string" ? "string" : e == null ? "null" : typeof e == "boolean" ? "boolean" : isNaN(e) ? typeof e == "object" ? "object" : "string" : "number";
}
var Lk = Ql(function(e) {
  return Zv(Gs(e, 1, bs, !0));
});
function En(e) {
  let { type: t } = e;
  return !t && e.const ? Rs(e.const) : !t && e.enum ? "string" : !t && (e.properties || e.additionalProperties || e.patternProperties) ? "object" : (Array.isArray(t) && (t.length === 2 && t.includes("null") ? t = t.find((i) => i !== "null") : t = t[0]), t);
}
function ir(e, t) {
  const i = Object.assign({}, e);
  return Object.keys(t).reduce((o, a) => {
    const l = e ? e[a] : {}, c = t[a];
    return e && a in e && xe(c) ? o[a] = ir(l, c) : e && t && (En(e) === "object" || En(t) === "object") && a === yv && Array.isArray(l) && Array.isArray(c) ? o[a] = Lk(l, c) : o[a] = c, o;
  }, i);
}
var Uk = "[object Number]";
function k0(e) {
  return typeof e == "number" || an(e) && or(e) == Uk;
}
function T0(e, t, i) {
  var o;
  if (e && i) {
    const a = re(e, i);
    if (a === void 0)
      return;
    for (let l = 0; l < t.length; l++) {
      const c = t[l], f = re(c, [Me, i], {});
      if (!(f.type === "object" || f.type === "array") && (f.const === a || !((o = f.enum) === null || o === void 0) && o.includes(a)))
        return l;
    }
  }
}
function Ed(e, t, i, o, a) {
  if (t === void 0)
    return 0;
  const l = T0(t, i, a);
  if (k0(l))
    return l;
  for (let c = 0; c < i.length; c++) {
    const f = i[c];
    if (a && Ae(f, [Me, a])) {
      const d = re(t, a), m = re(f, [Me, a], {});
      if (e.isValid(m, d, o))
        return c;
    } else if (f[Me]) {
      const d = {
        anyOf: Object.keys(f[Me]).map((y) => ({
          required: [y]
        }))
      };
      let m;
      if (f.anyOf) {
        const { ...y } = f;
        y.allOf ? y.allOf = y.allOf.slice() : y.allOf = [], y.allOf.push(d), m = y;
      } else
        m = Object.assign({}, f, d);
      if (delete m.required, e.isValid(m, t, o))
        return c;
    } else if (e.isValid(f, t, o))
      return c;
  }
  return 0;
}
function jt(e, t, i = {}, o, a, l = !1) {
  return Rn(e, t, i, o, void 0, void 0, a, l)[0];
}
function zk(e, t, i, o, a, l, c) {
  const { if: f, then: d, else: m, ...y } = t, h = e.isValid(f, l || {}, i);
  let S = [y], $ = [];
  if (o)
    d && typeof d != "boolean" && ($ = $.concat(Rn(e, d, i, l, o, a, c))), m && typeof m != "boolean" && ($ = $.concat(Rn(e, m, i, l, o, a, c)));
  else {
    const v = h ? d : m;
    v && typeof v != "boolean" && ($ = $.concat(Rn(e, v, i, l, o, a, c)));
  }
  return $.length && (S = $.map((v) => ir(y, v))), S.flatMap((v) => Rn(e, v, i, l, o, a, c));
}
function N0(e) {
  return e.reduce((i, o) => o.length > 1 ? o.flatMap((a) => Mv(i.length, (l) => [...i[l]].concat(a))) : (i.forEach((a) => a.push(o[0])), i), [[]]);
}
function I0(e, t) {
  return Object.keys(e.patternProperties).filter((i) => RegExp(i).test(t)).reduce((i, o) => (Be(i, [o], e.patternProperties[o]), i), {});
}
function Vk(e, t, i, o, a, l, c, f) {
  const d = j0(e, t, i, o, a, l, c, f);
  if (d.length > 1 || d[0] !== t)
    return d;
  if (Jf in t)
    return A0(e, t, i, o, a, l, c).flatMap((y) => Rn(e, y, i, l, o, a, c));
  if (Ur in t && Array.isArray(t[Ur])) {
    const m = t.allOf.map((h) => Rn(e, h, i, l, o, a, c));
    return N0(m).map((h) => ({
      ...t,
      allOf: h
    }));
  }
  return [t];
}
function j0(e, t, i, o, a, l, c, f) {
  const d = uo(t, i, a, void 0, f);
  return d !== t ? Rn(e, d, i, l, o, a, c, f) : [t];
}
function uo(e, t, i, o, a) {
  if (!xe(e))
    return e;
  let l = e;
  if (Ze in l) {
    const { $ref: c, ...f } = l;
    if (i.includes(c))
      return l;
    i.push(c), l = { ...C0(c, t, o), ...f }, Ke in l && (o = l[Ke]);
  }
  if (Me in l) {
    const c = [], f = UO(l[Me], (d, m, y) => {
      const h = [...i];
      d[y] = uo(m, t, h, o, a), c.push(h);
    }, {});
    rP(i, e0(sP(c))), l = { ...l, [Me]: f };
  }
  if (po in l && !Array.isArray(l.items) && typeof l.items != "boolean" && (l = {
    ...l,
    items: uo(l.items, t, i, o, a)
  }), a) {
    let c, f;
    be in e && Array.isArray(e[be]) ? (c = be, f = l[be]) : Ne in e && Array.isArray(e[Ne]) && (c = Ne, f = l[Ne]), c && f && (l = {
      ...l,
      [c]: f.map((d) => uo(d, t, i, o, a))
    });
  }
  return Ge(e, l) ? e : l;
}
function Bk(e, t, i, o, a) {
  const l = {
    ...t,
    properties: { ...t.properties }
  }, c = o && xe(o) ? o : {};
  return Object.keys(c).forEach((f) => {
    if (!(f in l.properties)) {
      if (Pf in l) {
        const d = I0(l, f);
        if (!dt(d)) {
          l.properties[f] = jt(e, { [Ur]: Object.values(d) }, i, re(c, [f]), a), Be(l.properties, [f, Fr], !0);
          return;
        }
      }
      if (Il in l && l.additionalProperties !== !1) {
        let d;
        typeof l.additionalProperties != "boolean" ? Ze in l.additionalProperties ? d = jt(e, { [Ze]: re(l.additionalProperties, [Ze]) }, i, c, a) : "type" in l.additionalProperties ? d = { ...l.additionalProperties } : be in l.additionalProperties || Ne in l.additionalProperties ? d = {
          type: "object",
          ...l.additionalProperties
        } : d = { type: Rs(re(c, [f])) } : d = { type: Rs(re(c, [f])) }, l.properties[f] = d, Be(l.properties, [f, Fr], !0);
      } else
        l.properties[f] = { type: "null" }, Be(l.properties, [f, Fr], !0);
    }
  }), l;
}
const { compareSchemaDefinitions: Kk, compareSchemaValues: Wk } = NP(), { mergeArrayOfSchemaDefinitions: Hk } = MP({
  intersectJson: $P(Wk),
  deduplicateJsonSchemaDef: t0(Kk)
}), qk = UP(Hk);
function Gk(e) {
  return qk(e);
}
function Rn(e, t, i, o, a = !1, l = [], c, f) {
  return xe(t) ? Vk(e, t, i, a, l, o, c, f).flatMap((m) => {
    var y;
    let h = m;
    if (g1 in h)
      return zk(e, h, i, a, l, o, c);
    if (Ur in h) {
      if (a) {
        const { allOf: $, ...v } = h;
        return [...$, v];
      }
      try {
        const $ = [], v = [];
        (y = h.allOf) === null || y === void 0 || y.forEach((w) => {
          typeof w == "object" && w.contains ? $.push(w) : v.push(w);
        }), $.length && (h = { ...h, allOf: v }), h = c ? c(h) : Gk(h), $.length && (h.allOf = $);
      } catch ($) {
        console.warn(`could not merge subschemas in allOf:
`, $);
        const { allOf: v, ...w } = h;
        return w;
      }
    }
    return Me in h && Pf in h && (h = Object.keys(h.properties).reduce(($, v) => {
      const w = I0($, v);
      return dt(w) || ($.properties[v] = jt(e, { allOf: [$.properties[v], ...Object.values(w)] }, i, re(o, [v]), c)), $;
    }, {
      ...h,
      properties: { ...h.properties }
    })), Pf in h || Il in h && h.additionalProperties !== !1 ? Bk(e, h, i, o, c) : h;
  }) : [{}];
}
function Yk(e, t, i, o, a) {
  let l;
  const { oneOf: c, anyOf: f, ...d } = t;
  if (Array.isArray(c) ? l = c : Array.isArray(f) && (l = f), l) {
    const m = a === void 0 && o ? {} : a, y = zn(t);
    l = l.map((S) => uo(S, i, []));
    const h = Ed(e, m, l, i, y);
    if (o)
      return l.map((S) => ir(d, S));
    t = ir(d, l[h]);
  }
  return [t];
}
function A0(e, t, i, o, a, l, c) {
  const { dependencies: f, ...d } = t;
  return Yk(e, d, i, o, l).flatMap((y) => x0(e, f, y, i, o, a, l, c));
}
function x0(e, t, i, o, a, l, c, f) {
  let d = [i];
  for (const m in t) {
    if (!a && re(c, [m]) === void 0 || i.properties && !(m in i.properties))
      continue;
    const [y, h] = wd(m, t);
    return Array.isArray(h) ? d[0] = Qk(i, h) : xe(h) && (d = Jk(e, i, o, m, h, a, l, c, f)), d.flatMap((S) => x0(e, y, S, o, a, l, c, f));
  }
  return d;
}
function Qk(e, t) {
  if (!t)
    return e;
  const i = Array.isArray(e.required) ? Array.from(/* @__PURE__ */ new Set([...e.required, ...t])) : t;
  return { ...e, required: i };
}
function Jk(e, t, i, o, a, l, c, f, d) {
  return Rn(e, a, i, f, l, c, d).flatMap((y) => {
    const { oneOf: h, ...S } = y;
    if (t = ir(t, S), h === void 0)
      return t;
    const $ = h.map((w) => typeof w == "boolean" || !(Ze in w) ? [w] : j0(e, w, i, l, c, f));
    return N0($).flatMap((w) => Xk(e, t, i, o, w, l, c, f, d));
  });
}
function Xk(e, t, i, o, a, l, c, f, d) {
  const m = a.filter((y) => {
    if (typeof y == "boolean" || !y || !y.properties)
      return !1;
    const { [o]: h } = y.properties;
    if (h) {
      const S = {
        type: "object",
        properties: {
          [o]: h
        }
      };
      return e.isValid(S, f, i) || l;
    }
    return !1;
  });
  return !l && m.length !== 1 ? (console.warn("ignoring oneOf in dependencies because there isn't exactly one subschema that is valid"), [t]) : m.flatMap((y) => {
    const h = y, [S] = wd(o, h.properties), $ = { ...h, properties: S };
    return Rn(e, $, i, f, l, c, d).map((w) => ir(t, w));
  });
}
function _s(e, t, i, o, a, l = {}, c) {
  if (Array.isArray(i[a])) {
    const d = zn(i) || o, m = i[a].map((h) => jt(e, h, t, l, c)), y = re(l, d);
    if (y !== void 0)
      return m.find((h) => xs(re(h, [Me, d, Vl], re(h, [Me, d, on])), y));
  }
}
function b0(e, t, i, o, a) {
  let l = i;
  if (Ae(i, Ze) && (l = jt(e, i, t, void 0, a)), dt(o))
    return l;
  const c = Array.isArray(o) ? o : o.split("."), [f, ...d] = c;
  if (f && Ae(l, f))
    return l = re(l, f), b0(e, t, l, d, a);
}
function El(e, t, i, o, a, l) {
  const c = b0(e, t, i, o, l);
  return c === void 0 ? a : c;
}
const og = { title: "!@#$_UNKNOWN_$#@!" };
function Zk(e, t, i, o, a = {}, l) {
  const c = Array.isArray(o) ? [...o] : o.split(".");
  let f = i;
  const d = c.pop();
  c.length && c.forEach((S) => {
    f = El(e, t, f, [Me, S], {}, l), Ae(f, Ne) ? f = _s(e, t, f, d, Ne, re(a, S), l) : Ae(f, be) && (f = _s(e, t, f, d, be, re(a, S), l));
  }), Ae(f, Ne) ? f = _s(e, t, f, d, Ne, a, l) : Ae(f, be) && (f = _s(e, t, f, d, be, a, l));
  let m = El(e, t, f, [Me, d], og, l);
  m === og && (m = void 0);
  const y = El(e, t, f, yv, [], l);
  let h;
  return m && Array.isArray(y) && (h = y.includes(d)), { field: m, isRequired: h };
}
function eT(e, t, i, o) {
  var a = -1, l = e == null ? 0 : e.length;
  for (o && l && (i = e[++a]); ++a < l; )
    i = t(i, e[a], a, e);
  return i;
}
function tT(e, t) {
  return function(i, o) {
    if (i == null)
      return i;
    if (!Ei(i))
      return e(i, o);
    for (var a = i.length, l = -1, c = Object(i); ++l < a && o(c[l], l, c) !== !1; )
      ;
    return i;
  };
}
var F0 = tT(zv);
function nT(e, t, i, o, a) {
  return a(e, function(l, c, f) {
    i = o ? (o = !1, l) : t(i, l, c, f);
  }), i;
}
function rT(e, t, i) {
  var o = yt(e) ? eT : nT, a = arguments.length < 3;
  return o(e, dd(t), i, a, F0);
}
const iT = {
  type: "object",
  $id: v1,
  properties: {
    __not_really_there__: {
      type: "number"
    }
  }
};
function Rf(e, t, i, o, a) {
  let l = 0;
  return i && (Fe(i.properties) ? l += rT(i.properties, (c, f, d) => {
    const m = re(o, d);
    if (typeof f == "boolean")
      return c;
    if (Ae(f, Ze)) {
      const y = jt(e, f, t, m, a);
      return c + Rf(e, t, y, m || {}, a);
    }
    if ((Ae(f, Ne) || Ae(f, be)) && m) {
      const y = Ae(f, Ne) ? Ne : be, h = zn(f);
      return c + Ds(e, t, m, re(f, y), -1, h, a);
    }
    if (f.type === "object")
      return Fe(m) && (c += 1), c + Rf(e, t, f, m, a);
    if (f.type === Rs(m)) {
      let y = c + 1;
      return f.default ? y += m === f.default ? 1 : -1 : f.const && (y += m === f.const ? 1 : -1), y;
    }
    return c;
  }, 0) : Vr(i.type) && i.type === Rs(o) && (l += 1)), l;
}
function Ds(e, t, i, o, a = -1, l, c) {
  const f = o.map((S) => uo(S, t, [])), d = T0(i, o, l);
  if (k0(d))
    return d;
  const m = f.reduce((S, $, v) => (Ed(e, i, [iT, $], t, l) === 1 && S.push(v), S), []);
  if (m.length === 1)
    return m[0];
  m.length || Mv(f.length, (S) => m.push(S));
  const y = /* @__PURE__ */ new Set(), { bestIndex: h } = m.reduce((S, $) => {
    const { bestScore: v } = S, w = f[$], _ = Rf(e, t, w, i, c);
    return y.add(_), _ > v ? { bestIndex: $, bestScore: _ } : S;
  }, { bestIndex: a, bestScore: 0 });
  return y.size === 1 && a >= 0 ? a : h;
}
function $d(e) {
  return Array.isArray(e.items) && e.items.length > 0 && e.items.every((t) => xe(t));
}
function Rl(e) {
  return e == null;
}
function Ms(e, t, i = !1, o = !1, a = !1) {
  if (Array.isArray(t)) {
    const l = Array.isArray(e) ? e : [], c = a ? l : t, f = a ? t : l, d = c.map((m, y) => f[y] !== void 0 ? Ms(l[y], t[y], i, o, a) : m);
    return (i || a) && d.length < f.length && d.push(...f.slice(d.length)), d;
  }
  if (xe(t)) {
    const l = Object.assign({}, e);
    return Object.keys(t).reduce((c, f) => {
      var d;
      const m = re(t, f), y = xe(e) && f in e, h = f in t, S = (d = re(e, f)) !== null && d !== void 0 ? d : {}, $ = y && Object.entries(S).some(([, _]) => xe(_)), v = y && xe(re(e, f)), w = h && xe(m);
      return v && w && !$ ? (c[f] = {
        ...re(e, f),
        ...m
      }, c) : (c[f] = Ms(
        re(e, f),
        m,
        i,
        o,
        // overrideFormDataWithDefaults can be true only when the key value exists in defaults
        // Or if the key value doesn't exist in formData
        a && (y || !h)
      ), c);
    }, l);
  }
  return o && (e !== void 0 && Rl(t) || typeof t == "number" && isNaN(t)) || a && !Rl(t) ? e : t;
}
function Ls(e, t, i = !1) {
  return Object.keys(t).reduce((o, a) => {
    const l = e ? e[a] : {}, c = t[a];
    if (e && a in e && xe(c))
      o[a] = Ls(l, c, i);
    else if (i && Array.isArray(l) && Array.isArray(c)) {
      let f = c;
      i === "preventDuplicates" && (f = c.reduce((d, m) => (l.includes(m) || d.push(m), d), [])), o[a] = l.concat(f);
    } else
      o[a] = c;
    return o;
  }, Object.assign({}, e));
}
function R0(e) {
  return Array.isArray(e.enum) && e.enum.length === 1 || on in e;
}
function Od(e, t, i = {}, o) {
  const a = jt(e, t, i, void 0, o), l = a.oneOf || a.anyOf;
  return Array.isArray(a.enum) ? !0 : Array.isArray(l) ? l.every((c) => typeof c != "boolean" && R0(c)) : !1;
}
function Pd(e, t, i, o) {
  return !t.uniqueItems || !t.items || typeof t.items == "boolean" ? !1 : Od(e, t.items, i, o);
}
function D0(e) {
  const t = e[on], i = En(e);
  return xe(t) && Vr(t == null ? void 0 : t.$data) && i !== "object" && i !== "array";
}
function oT(e) {
  if (y1 in e && Array.isArray(e.enum) && e.enum.length === 1)
    return e.enum[0];
  if (on in e)
    return e.const;
  throw new Error("schema cannot be inferred as a constant");
}
function yo(e, t) {
  if (e.enum) {
    let l;
    if (t) {
      const { enumNames: c } = Ee(t);
      l = c;
    }
    return e.enum.map((c, f) => ({ label: (l == null ? void 0 : l[f]) || String(c), value: c }));
  }
  let i, o;
  e.anyOf ? (i = e.anyOf, o = t == null ? void 0 : t.anyOf) : e.oneOf && (i = e.oneOf, o = t == null ? void 0 : t.oneOf);
  let a = zn(e);
  if (t) {
    const { optionsSchemaSelector: l = a } = Ee(t);
    a = l;
  }
  return i && i.map((l, c) => {
    const { title: f } = Ee(o == null ? void 0 : o[c]), d = l;
    let m, y = f;
    if (a) {
      const h = re(d, [Me, a], {});
      m = re(h, Vl, re(h, on)), y = y || (h == null ? void 0 : h.title) || d.title || String(m);
    } else
      m = oT(d), y = y || d.title || String(m);
    return {
      schema: d,
      label: y,
      value: m
    };
  });
}
const sT = ["string", "number", "integer", "boolean", "null"];
var go;
(function(e) {
  e[e.Ignore = 0] = "Ignore", e[e.Invert = 1] = "Invert", e[e.Fallback = 2] = "Fallback";
})(go || (go = {}));
function cf(e, t = go.Ignore, i = -1) {
  if (i >= 0) {
    if (Array.isArray(e.items) && i < e.items.length) {
      const o = e.items[i];
      if (typeof o != "boolean")
        return o;
    }
  } else if (e.items && !Array.isArray(e.items) && typeof e.items != "boolean")
    return e.items;
  return t !== go.Ignore && xe(e.additionalItems) ? e.additionalItems : {};
}
function M0(e, t) {
  const { default: i, type: o } = e;
  return Array.isArray(o) && o.includes("null") && dt(t) && i === null ? null : t;
}
function sg(e, t, i, o, a, l = [], c = {}, f = !1, d = !1) {
  const { emptyObjectFields: m = "populateAllDefaults" } = c;
  if (o === !0 || f)
    e[t] = i;
  else if (o === "excludeObjectChildren")
    (d && i !== void 0 || !xe(i) || !dt(i)) && (e[t] = i);
  else if (m !== "skipDefaults") {
    const y = a === void 0 ? l.includes(t) : a;
    xe(i) ? m === "skipEmptyDefaults" ? dt(i) || (e[t] = i) : (!dt(i) || l.includes(t)) && (y || m !== "populateRequiredDefaults") && (e[t] = i) : (
      // Store computedDefault if it's a defined primitive (e.g., true) and satisfies certain conditions
      // Condition 1: computedDefault is not undefined
      // Condition 2: If emptyObjectFields is 'populateAllDefaults' or 'skipEmptyDefaults)
      // Or if isSelfOrParentRequired is 'true' and the key is a required field
      i !== void 0 && (m === "populateAllDefaults" || m === "skipEmptyDefaults" || y && l.includes(t)) && (e[t] = i)
    );
  }
}
function Dr(e, t, i = {}) {
  const { parentDefaults: o, rawFormData: a, rootSchema: l = {}, includeUndefinedValues: c = !1, _recurseList: f = [], experimental_defaultFormStateBehavior: d = void 0, experimental_customMergeAllOf: m = void 0, required: y, shouldMergeDefaultsIntoFormData: h = !1, initialDefaultsGenerated: S } = i;
  let $ = xe(a) ? a : {};
  const v = xe(t) ? t : {};
  let w = o, _ = null, E = d, k = f;
  if (v[on] !== void 0 && (d == null ? void 0 : d.constAsDefaults) !== "never" && !D0(v))
    w = v[on];
  else if (xe(w) && xe(v.default))
    w = Ls(w, v.default);
  else if (Vl in v && !v[be] && !v[Ne] && !v[Ze])
    w = v.default;
  else if (Ze in v) {
    const N = v[Ze];
    f.includes(N) || (k = f.concat(N), _ = C0(N, l)), _ && !w && (w = v.default), h && _ && !xe(a) && ($ = a);
  } else if (Jf in v) {
    const N = {
      ...ag(e, v, i, w),
      ...$
    };
    _ = A0(e, v, l, !1, [], N, m)[0];
  } else if ($d(v))
    w = v.items.map((N, x) => Dr(e, N, {
      rootSchema: l,
      includeUndefinedValues: c,
      _recurseList: f,
      experimental_defaultFormStateBehavior: d,
      experimental_customMergeAllOf: m,
      parentDefaults: Array.isArray(o) ? o[x] : void 0,
      rawFormData: $,
      required: y,
      shouldMergeDefaultsIntoFormData: h
    }));
  else if (Ne in v) {
    const { oneOf: N, ...x } = v;
    if (N.length === 0)
      return;
    const F = zn(v), { type: V = "null" } = x;
    !Array.isArray(V) && sT.includes(V) && (E == null ? void 0 : E.constAsDefaults) === "skipOneOf" && (E = {
      ...E,
      constAsDefaults: "never"
    }), _ = N[Ds(e, l, a ?? v.default, N, 0, F, m)], _ = ir(x, _);
  } else if (be in v) {
    const { anyOf: N, ...x } = v;
    if (N.length === 0)
      return;
    const F = zn(v);
    _ = N[Ds(e, l, a ?? v.default, N, 0, F, m)], _ = ir(x, _);
  }
  if (_)
    return Dr(e, _, {
      rootSchema: l,
      includeUndefinedValues: c,
      _recurseList: k,
      experimental_defaultFormStateBehavior: E,
      experimental_customMergeAllOf: m,
      parentDefaults: w,
      rawFormData: a ?? $,
      required: y,
      shouldMergeDefaultsIntoFormData: h,
      initialDefaultsGenerated: S
    });
  w === void 0 && (w = v.default);
  const j = ag(e, v, i, w);
  let T = j ?? w;
  if (h) {
    const { arrayMinItems: N = {} } = d || {}, { mergeExtraDefaults: x } = N, F = aT(e, v, l, a, d, m);
    (!xe(a) || Ur in v) && (T = Ms(T, F, x, !0));
  }
  return T;
}
function aT(e, t, i, o, a, l) {
  const c = !R0(t) && Od(e, t, i, l);
  let f = o;
  if (c) {
    const m = yo(t);
    f = (m == null ? void 0 : m.some((h) => Ge(h.value, o))) ? o : void 0;
  }
  return t[on] && (a == null ? void 0 : a.constAsDefaults) === "always" && (f = t.const), f;
}
function lT(e, t, { rawFormData: i, rootSchema: o = {}, includeUndefinedValues: a = !1, _recurseList: l = [], experimental_defaultFormStateBehavior: c = void 0, experimental_customMergeAllOf: f = void 0, required: d, shouldMergeDefaultsIntoFormData: m, initialDefaultsGenerated: y } = {}, h) {
  {
    const S = xe(i) ? i : {}, $ = t, v = (c == null ? void 0 : c.allOf) === "populateDefaults" && Ur in $ ? jt(e, $, o, S, f) : $, w = v[on], _ = Object.keys(v.properties || {}).reduce((E, k) => {
      var j;
      const T = re(v, [Me, k], {}), N = xe(w) && w[k] !== void 0, x = (xe(T) && on in T || N) && (c == null ? void 0 : c.constAsDefaults) !== "never" && !D0(T), F = Dr(e, T, {
        rootSchema: o,
        _recurseList: l,
        experimental_defaultFormStateBehavior: c,
        experimental_customMergeAllOf: f,
        includeUndefinedValues: a === !0,
        parentDefaults: re(h, [k]),
        rawFormData: re(S, [k]),
        required: (j = v.required) === null || j === void 0 ? void 0 : j.includes(k),
        shouldMergeDefaultsIntoFormData: m,
        initialDefaultsGenerated: y
      });
      return sg(E, k, F, a, d, v.required, c, x, (T == null ? void 0 : T.type) === "null"), E;
    }, {});
    if (v.additionalProperties && !y) {
      const E = xe(v.additionalProperties) ? v.additionalProperties : {}, k = /* @__PURE__ */ new Set();
      xe(h) && Object.keys(h).filter((T) => !v.properties || !v.properties[T]).forEach((T) => k.add(T));
      const j = [];
      Object.keys(S).filter((T) => !v.properties || !v.properties[T]).forEach((T) => {
        k.add(T), j.push(T);
      }), k.forEach((T) => {
        var N;
        const x = Dr(e, E, {
          rootSchema: o,
          _recurseList: l,
          experimental_defaultFormStateBehavior: c,
          experimental_customMergeAllOf: f,
          includeUndefinedValues: a === !0,
          parentDefaults: re(h, [T]),
          rawFormData: re(S, [T]),
          required: (N = v.required) === null || N === void 0 ? void 0 : N.includes(T),
          shouldMergeDefaultsIntoFormData: m,
          initialDefaultsGenerated: y
        });
        sg(_, T, x, a, d, j);
      });
    }
    return M0(t, _);
  }
}
function uT(e, t, { rawFormData: i, rootSchema: o = {}, _recurseList: a = [], experimental_defaultFormStateBehavior: l = void 0, experimental_customMergeAllOf: c = void 0, required: f, requiredAsRoot: d = !1, shouldMergeDefaultsIntoFormData: m, initialDefaultsGenerated: y } = {}, h) {
  var S, $;
  const v = t, w = (S = l == null ? void 0 : l.arrayMinItems) !== null && S !== void 0 ? S : {}, { populate: _, mergeExtraDefaults: E } = w, k = _ === "never", j = _ === "requiredOnly", T = _ === "all" || !k && !j, N = ($ = w == null ? void 0 : w.computeSkipPopulate) !== null && $ !== void 0 ? $ : () => !1, F = (l == null ? void 0 : l.emptyObjectFields) === "skipEmptyDefaults" ? void 0 : [];
  if (Array.isArray(h) && (h = h.map((Q, H) => {
    const q = cf(v, go.Fallback, H);
    return Dr(e, q, {
      rootSchema: o,
      _recurseList: a,
      experimental_defaultFormStateBehavior: l,
      experimental_customMergeAllOf: c,
      parentDefaults: Q,
      required: f,
      shouldMergeDefaultsIntoFormData: m,
      initialDefaultsGenerated: y
    });
  })), Array.isArray(i)) {
    const Q = cf(v);
    if (k)
      h = i;
    else {
      const H = i.map((le, ie) => Dr(e, Q, {
        rootSchema: o,
        _recurseList: a,
        experimental_defaultFormStateBehavior: l,
        experimental_customMergeAllOf: c,
        rawFormData: le,
        parentDefaults: re(h, [ie]),
        required: f,
        shouldMergeDefaultsIntoFormData: m,
        initialDefaultsGenerated: y
      }));
      h = Ms(h, H, (j && f || T) && E);
    }
  }
  if ((xe(v) && on in v && (l == null ? void 0 : l.constAsDefaults) !== "never") === !1) {
    if (k)
      return h ?? F;
    if (j && !f)
      return h || void 0;
  }
  let U;
  const G = Array.isArray(h) ? h.length : 0;
  if (!v.minItems || Pd(e, v, o, c) || N(e, v, o) || v.minItems <= G)
    U = h || !f && !d ? h : F;
  else {
    const Q = h || [], H = cf(v, go.Invert), q = H.default, le = Array.from({ length: v.minItems - G }, () => Dr(e, H, {
      parentDefaults: q,
      rootSchema: o,
      _recurseList: a,
      experimental_defaultFormStateBehavior: l,
      experimental_customMergeAllOf: c,
      required: f,
      shouldMergeDefaultsIntoFormData: m
    }));
    U = Q.concat(le);
  }
  return M0(t, U);
}
function ag(e, t, i = {}, o) {
  switch (En(t)) {
    case "object":
      return lT(e, t, i, o);
    case "array":
      return uT(e, t, i, o);
  }
}
function L0(e, t, i, o, a = !1, l, c, f) {
  if (!xe(t))
    throw new Error("Invalid schema: " + t);
  const d = jt(e, t, o, i, c), m = Dr(e, d, {
    rootSchema: o,
    includeUndefinedValues: a,
    experimental_defaultFormStateBehavior: l,
    experimental_customMergeAllOf: c,
    rawFormData: i,
    shouldMergeDefaultsIntoFormData: !0,
    initialDefaultsGenerated: f,
    requiredAsRoot: !0
  });
  if (d.type !== "object" && xe(d.default))
    return {
      ...m,
      ...i
    };
  if (xe(i) || Array.isArray(i)) {
    const { mergeDefaultsIntoFormData: y } = l || {};
    return Ms(
      m,
      i,
      !0,
      y === "useDefaultIfFormDataUndefined",
      !0
    );
  }
  return m;
}
function U0(e = {}) {
  return (
    // TODO: Remove the `&& uiSchema['ui:widget'] !== 'hidden'` once we support hidden widgets for arrays.
    // https://rjsf-team.github.io/react-jsonschema-form/docs/usage/widgets/#hidden-widgets
    "widget" in Ee(e) && Ee(e).widget !== "hidden"
  );
}
function z0(e, t, i = {}, o, a) {
  if (i[Zf] === "files")
    return !0;
  if (t.items) {
    const l = jt(e, t.items, o, void 0, a);
    return l.type === "string" && l.format === "data-url";
  }
  return !1;
}
function cT(e, t, i = {}, o, a, l) {
  const c = Ee(i, a), { label: f = !0 } = c;
  let d = !!f;
  if (d) {
    const m = En(t), y = re(t, Fr, !1);
    m === "array" && (d = y || Pd(e, t, o, l) || z0(e, t, i, o, l) || U0(i)), m === "object" && (d = y), m === "boolean" && i && !i[Zf] && (d = !1), i && i[w1] && (d = !1);
  }
  return d;
}
const eo = Symbol("no Value");
function Df(e, t, i, o, a = {}, l) {
  let c;
  if (Ae(i, Me)) {
    const f = {};
    if (Ae(o, Me)) {
      const y = re(o, Me, {});
      Object.keys(y).forEach((h) => {
        Ae(a, h) && (f[h] = void 0);
      });
    }
    const d = Object.keys(re(i, Me, {})), m = {};
    d.forEach((y) => {
      const h = re(a, y);
      let S = re(o, [Me, y], {}), $ = re(i, [Me, y], {});
      Ae(S, Ze) && (S = jt(e, S, t, h, l)), Ae($, Ze) && ($ = jt(e, $, t, h, l));
      const v = re(S, "type"), w = re($, "type");
      if (!v || v === w)
        if (Ae(f, y) && delete f[y], w === "object" || w === "array" && Array.isArray(h)) {
          const _ = Df(e, t, $, S, h, l);
          (_ !== void 0 || w === "array") && (m[y] = _);
        } else {
          const _ = re($, "default", eo), E = re(S, "default", eo);
          _ !== eo && _ !== h && (E === h ? f[y] = _ : re($, "readOnly") === !0 && (f[y] = void 0));
          const k = re($, "const", eo), j = re(S, "const", eo);
          k !== eo && k !== h && (f[y] = j === h ? k : void 0);
        }
    }), c = {
      ...typeof a == "string" || Array.isArray(a) ? void 0 : a,
      ...f,
      ...m
    };
  } else if (re(o, "type") === "array" && re(i, "type") === "array" && Array.isArray(a)) {
    let f = re(o, "items"), d = re(i, "items");
    if (typeof f == "object" && typeof d == "object" && !Array.isArray(f) && !Array.isArray(d)) {
      Ae(f, Ze) && (f = jt(e, f, t, a, l)), Ae(d, Ze) && (d = jt(e, d, t, a, l));
      const m = re(f, "type"), y = re(d, "type");
      if (!m || m === y) {
        const h = re(i, "maxItems", -1);
        y === "object" ? c = a.reduce((S, $) => {
          const v = Df(e, t, d, f, $, l);
          return v !== void 0 && (h < 0 || S.length < h) && S.push(v), S;
        }, []) : c = h > 0 && a.length > h ? a.slice(0, h) : a;
      }
    } else typeof f == "boolean" && typeof d == "boolean" && f === d && (c = a);
  }
  return c;
}
function ui(e, t, i, o, a, l = [], c) {
  if (Ze in t || Jf in t || Ur in t) {
    const d = jt(e, t, o, a, c);
    if (l.findIndex((y) => Ge(y, d)) === -1)
      return ui(e, d, i, o, a, l.concat(d), c);
  }
  let f = {
    [gl]: i.replace(/^\./, "")
  };
  if (Ne in t || be in t) {
    const d = Ne in t ? t.oneOf : t.anyOf, m = zn(t), y = Ds(e, o, a, d, 0, m, c), h = d[y];
    f = {
      ...f,
      ...ui(e, h, i, o, a, l, c)
    };
  }
  if (Il in t && t[Il] !== !1 && Be(f, Xf, !0), po in t && Array.isArray(a)) {
    const { items: d, additionalItems: m } = t;
    Array.isArray(d) ? a.forEach((y, h) => {
      d[h] ? f[h] = ui(e, d[h], `${i}.${h}`, o, y, l, c) : m ? f[h] = ui(e, m, `${i}.${h}`, o, y, l, c) : console.warn(`Unable to generate path schema for "${i}.${h}". No schema defined for it`);
    }) : a.forEach((y, h) => {
      f[h] = ui(e, d, `${i}.${h}`, o, y, l, c);
    });
  } else if (Me in t)
    for (const d in t.properties) {
      const m = re(t, [Me, d], {});
      f[d] = ui(
        e,
        m,
        `${i}.${d}`,
        o,
        // It's possible that formData is not an object -- this can happen if an
        // array item has just been added, but not populated with data yet
        re(a, [d]),
        l,
        c
      );
    }
  return f;
}
function fT(e, t, i = "", o, a, l) {
  return ui(e, t, i, o, a, void 0, l);
}
class dT {
  /** Constructs the `SchemaUtils` instance with the given `validator` and `rootSchema` stored as instance variables
   *
   * @param validator - An implementation of the `ValidatorType` interface that will be forwarded to all the APIs
   * @param rootSchema - The root schema that will be forwarded to all the APIs
   * @param experimental_defaultFormStateBehavior - Configuration flags to allow users to override default form state behavior
   * @param [experimental_customMergeAllOf] - Optional function that allows for custom merging of `allOf` schemas
   */
  constructor(t, i, o, a) {
    i && i[ys] === vl ? this.rootSchema = Ff(i, re(i, Ke, "#")) : this.rootSchema = i, this.validator = t, this.experimental_defaultFormStateBehavior = o, this.experimental_customMergeAllOf = a;
  }
  /** Returns the `rootSchema` in the `SchemaUtilsType`
   *
   * @returns - The `rootSchema`
   */
  getRootSchema() {
    return this.rootSchema;
  }
  /** Returns the `ValidatorType` in the `SchemaUtilsType`
   *
   * @returns - The `ValidatorType`
   */
  getValidator() {
    return this.validator;
  }
  /** Determines whether either the `validator` and `rootSchema` differ from the ones associated with this instance of
   * the `SchemaUtilsType`. If either `validator` or `rootSchema` are falsy, then return false to prevent the creation
   * of a new `SchemaUtilsType` with incomplete properties.
   *
   * @param validator - An implementation of the `ValidatorType` interface that will be compared against the current one
   * @param rootSchema - The root schema that will be compared against the current one
   * @param [experimental_defaultFormStateBehavior] Optional configuration object, if provided, allows users to override default form state behavior
   * @param [experimental_customMergeAllOf] - Optional function that allows for custom merging of `allOf` schemas
   * @returns - True if the `SchemaUtilsType` differs from the given `validator` or `rootSchema`
   */
  doesSchemaUtilsDiffer(t, i, o = {}, a) {
    return !t || !i ? !1 : this.validator !== t || !Ge(this.rootSchema, i) || !Ge(this.experimental_defaultFormStateBehavior, o) || this.experimental_customMergeAllOf !== a;
  }
  /** Finds the field specified by the `path` within the root or recursed `schema`. If there is no field for the specified
   * `path`, then the default `{ field: undefined, isRequired: undefined }` is returned. It determines whether a leaf
   * field is in the `required` list for its parent and if so, it is marked as required on return.
   *
   * @param schema - The current node within the JSON schema
   * @param path - The remaining keys in the path to the desired field
   * @param [formData] - The form data that is used to determine which oneOf option
   * @returns - An object that contains the field and its required state. If no field can be found then
   *            `{ field: undefined, isRequired: undefined }` is returned.
   */
  findFieldInSchema(t, i, o) {
    return Zk(this.validator, this.rootSchema, t, i, o, this.experimental_customMergeAllOf);
  }
  /** Finds the oneOf option inside the `schema['any/oneOf']` list which has the `properties[selectorField].default` that
   * matches the `formData[selectorField]` value. For the purposes of this function, `selectorField` is either
   * `schema.discriminator.propertyName` or `fallbackField`.
   *
   * @param schema - The schema element in which to search for the selected oneOf option
   * @param fallbackField - The field to use as a backup selector field if the schema does not have a required field
   * @param xxx - Either `oneOf` or `anyOf`, defines which value is being sought
   * @param [formData={}] - The form data that is used to determine which oneOf option
   * @returns - The anyOf/oneOf option that matches the selector field in the schema or undefined if nothing is selected
   */
  findSelectedOptionInXxxOf(t, i, o, a) {
    return _s(this.validator, this.rootSchema, t, i, o, a, this.experimental_customMergeAllOf);
  }
  /** Returns the superset of `formData` that includes the given set updated to include any missing fields that have
   * computed to have defaults provided in the `schema`.
   *
   * @param schema - The schema for which the default state is desired
   * @param [formData] - The current formData, if any, onto which to provide any missing defaults
   * @param [includeUndefinedValues=false] - Optional flag, if true, cause undefined values to be added as defaults.
   *          If "excludeObjectChildren", pass `includeUndefinedValues` as false when computing defaults for any nested
   *          object properties.
   * @param initialDefaultsGenerated - Indicates whether or not initial defaults have been generated
   * @returns - The resulting `formData` with all the defaults provided
   */
  getDefaultFormState(t, i, o = !1, a) {
    return L0(this.validator, t, i, this.rootSchema, o, this.experimental_defaultFormStateBehavior, this.experimental_customMergeAllOf, a);
  }
  /** Determines whether the combination of `schema` and `uiSchema` properties indicates that the label for the `schema`
   * should be displayed in a UI.
   *
   * @param schema - The schema for which the display label flag is desired
   * @param [uiSchema] - The UI schema from which to derive potentially displayable information
   * @param [globalOptions={}] - The optional Global UI Schema from which to get any fallback `xxx` options
   * @returns - True if the label should be displayed or false if it should not
   */
  getDisplayLabel(t, i, o) {
    return cT(this.validator, t, i, this.rootSchema, o, this.experimental_customMergeAllOf);
  }
  /** Determines which of the given `options` provided most closely matches the `formData`.
   * Returns the index of the option that is valid and is the closest match, or 0 if there is no match.
   *
   * The closest match is determined using the number of matching properties, and more heavily favors options with
   * matching readOnly, default, or const values.
   *
   * @param formData - The form data associated with the schema
   * @param options - The list of options that can be selected from
   * @param [selectedOption] - The index of the currently selected option, defaulted to -1 if not specified
   * @param [discriminatorField] - The optional name of the field within the options object whose value is used to
   *          determine which option is selected
   * @returns - The index of the option that is the closest match to the `formData` or the `selectedOption` if no match
   */
  getClosestMatchingOption(t, i, o, a) {
    return Ds(this.validator, this.rootSchema, t, i, o, a, this.experimental_customMergeAllOf);
  }
  /** Given the `formData` and list of `options`, attempts to find the index of the first option that matches the data.
   * Always returns the first option if there is nothing that matches.
   *
   * @param formData - The current formData, if any, used to figure out a match
   * @param options - The list of options to find a matching options from
   * @param [discriminatorField] - The optional name of the field within the options object whose value is used to
   *          determine which option is selected
   * @returns - The firstindex of the matched option or 0 if none is available
   */
  getFirstMatchingOption(t, i, o) {
    return Ed(this.validator, t, i, this.rootSchema, o);
  }
  getFromSchema(t, i, o) {
    return El(
      this.validator,
      this.rootSchema,
      t,
      i,
      // @ts-expect-error TS2769: No overload matches this call
      o,
      this.experimental_customMergeAllOf
    );
  }
  /** Checks to see if the `schema` and `uiSchema` combination represents an array of files
   *
   * @param schema - The schema for which check for array of files flag is desired
   * @param [uiSchema] - The UI schema from which to check the widget
   * @returns - True if schema/uiSchema contains an array of files, otherwise false
   */
  isFilesArray(t, i) {
    return z0(this.validator, t, i, this.rootSchema, this.experimental_customMergeAllOf);
  }
  /** Checks to see if the `schema` combination represents a multi-select
   *
   * @param schema - The schema for which check for a multi-select flag is desired
   * @returns - True if schema contains a multi-select, otherwise false
   */
  isMultiSelect(t) {
    return Pd(this.validator, t, this.rootSchema, this.experimental_customMergeAllOf);
  }
  /** Checks to see if the `schema` combination represents a select
   *
   * @param schema - The schema for which check for a select flag is desired
   * @returns - True if schema contains a select, otherwise false
   */
  isSelect(t) {
    return Od(this.validator, t, this.rootSchema, this.experimental_customMergeAllOf);
  }
  /** Retrieves an expanded schema that has had all of its conditions, additional properties, references and
   * dependencies resolved and merged into the `schema` given a `rawFormData` that is used to do the potentially
   * recursive resolution.
   *
   * @param schema - The schema for which retrieving a schema is desired
   * @param [rawFormData] - The current formData, if any, to assist retrieving a schema
   * @param [resolveAnyOfOrOneOfRefs] - Optional flag indicating whether to resolved refs in anyOf/oneOf lists
   * @returns - The schema having its conditions, additional properties, references and dependencies resolved
   */
  retrieveSchema(t, i, o) {
    return jt(this.validator, t, this.rootSchema, i, this.experimental_customMergeAllOf, o);
  }
  /** Sanitize the `data` associated with the `oldSchema` so it is considered appropriate for the `newSchema`. If the
   * new schema does not contain any properties, then `undefined` is returned to clear all the form data. Due to the
   * nature of schemas, this sanitization happens recursively for nested objects of data. Also, any properties in the
   * old schemas that are non-existent in the new schema are set to `undefined`.
   *
   * @param [newSchema] - The new schema for which the data is being sanitized
   * @param [oldSchema] - The old schema from which the data originated
   * @param [data={}] - The form data associated with the schema, defaulting to an empty object when undefined
   * @returns - The new form data, with all the fields uniquely associated with the old schema set
   *      to `undefined`. Will return `undefined` if the new schema is not an object containing properties.
   */
  sanitizeDataForNewSchema(t, i, o) {
    return Df(this.validator, this.rootSchema, t, i, o, this.experimental_customMergeAllOf);
  }
  /** Generates an `PathSchema` object for the `schema`, recursively
   *
   * @param schema - The schema for which the display label flag is desired
   * @param [name] - The base name for the schema
   * @param [formData] - The current formData, if any, onto which to provide any missing defaults
   * @returns - The `PathSchema` object for the `schema`
   */
  toPathSchema(t, i, o) {
    return fT(this.validator, t, i, this.rootSchema, o, this.experimental_customMergeAllOf);
  }
}
function pT(e, t, i = {}, o) {
  return new dT(e, t, i, o);
}
function hT(e) {
  var t;
  if (e.indexOf("data:") === -1)
    throw new Error("File is invalid: URI must be a dataURI");
  const o = e.slice(5).split(";base64,");
  if (o.length !== 2)
    throw new Error("File is invalid: dataURI must be base64");
  const [a, l] = o, [c, ...f] = a.split(";"), d = c || "", m = decodeURI(
    // parse the parameters into key-value pairs, find a key, and extract a value
    // if no key is found, then the name is unknown
    ((t = f.map((y) => y.split("=")).find(([y]) => y === "name")) === null || t === void 0 ? void 0 : t[1]) || "unknown"
  );
  try {
    const y = atob(l), h = new Array(y.length);
    for (let $ = 0; $ < y.length; $++)
      h[$] = y.charCodeAt($);
    return { blob: new window.Blob([new Uint8Array(h)], { type: d }), name: m };
  } catch (y) {
    throw new Error("File is invalid: " + y.message);
  }
}
function Ar(e, t) {
  let i = String(e);
  for (; i.length < t; )
    i = "0" + i;
  return i;
}
function V0(e, t) {
  if (e <= 0 && t <= 0)
    e = (/* @__PURE__ */ new Date()).getFullYear() + e, t = (/* @__PURE__ */ new Date()).getFullYear() + t;
  else if (e < 0 || t < 0)
    throw new Error(`Both start (${e}) and stop (${t}) must both be <= 0 or > 0, got one of each`);
  if (e > t)
    return V0(t, e).reverse();
  const i = [];
  for (let o = e; o <= t; o++)
    i.push({ value: o, label: Ar(o, 2) });
  return i;
}
function lg(e, t) {
  if (Object.is(e, t))
    return !0;
  if (e == null || t == null || typeof e != "object" || typeof t != "object")
    return !1;
  const i = Object.keys(e), o = Object.keys(t);
  if (i.length !== o.length)
    return !1;
  for (let a = 0; a < i.length; a++) {
    const l = i[a];
    if (!Object.prototype.hasOwnProperty.call(t, l) || !Object.is(e[l], t[l]))
      return !1;
  }
  return !0;
}
function mT(e, t) {
  let i = e;
  if (Array.isArray(t)) {
    const o = i.split(/(%\d)/);
    t.forEach((a, l) => {
      const c = o.findIndex((f) => f === `%${l + 1}`);
      c >= 0 && (o[c] = a);
    }), i = o.join("");
  }
  return i;
}
function yT(e, t) {
  return mT(e, t);
}
function Un(e, t = [], i) {
  if (Array.isArray(e))
    return e.map((l) => Un(l, t)).filter((l) => l !== i);
  const o = e === "" || e === null ? -1 : Number(e), a = t[o];
  return a ? a.value : i;
}
function gT(e, t, i = []) {
  const o = Un(e, i);
  return Array.isArray(t) ? t.filter((a) => !Ge(a, o)) : Ge(o, t) ? void 0 : t;
}
function Cd(e, t) {
  return Array.isArray(t) ? t.some((i) => Ge(i, e)) : Ge(t, e);
}
function vT(e, t = [], i = !1) {
  const o = t.map((a, l) => Cd(a.value, e) ? String(l) : void 0).filter((a) => typeof a < "u");
  return i ? o : o[0];
}
function _T(e, t, i = []) {
  const o = Un(e, i);
  if (!Rl(o)) {
    const a = i.findIndex((f) => o === f.value), l = i.map(({ value: f }) => f);
    return t.slice(0, a).concat(o, t.slice(a)).sort((f, d) => +(l.indexOf(f) > l.indexOf(d)));
  }
  return t;
}
var ST = 1, wT = 4;
function kd(e) {
  return Es(e, ST | wT);
}
function ET(e, t, i, o) {
  return o = typeof o == "function" ? o : void 0, e == null ? e : cd(e, t, i, o);
}
class B0 {
  /** Construct an `ErrorSchemaBuilder` with an optional initial set of errors in an `ErrorSchema`.
   *
   * @param [initialSchema] - The optional set of initial errors, that will be cloned into the class
   */
  constructor(t) {
    this.errorSchema = {}, this.resetAllErrors(t);
  }
  /** Returns the `ErrorSchema` that has been updated by the methods of the `ErrorSchemaBuilder`
   */
  get ErrorSchema() {
    return this.errorSchema;
  }
  /** Will get an existing `ErrorSchema` at the specified `pathOfError` or create and return one.
   *
   * @param [pathOfError] - The optional path into the `ErrorSchema` at which to add the error(s)
   * @returns - The error block for the given `pathOfError` or the root if not provided
   * @private
   */
  getOrCreateErrorBlock(t) {
    let o = Array.isArray(t) && t.length > 0 || typeof t == "string" ? re(this.errorSchema, t) : this.errorSchema;
    return !o && t && (o = {}, ET(this.errorSchema, t, o, Object)), o;
  }
  /** Resets all errors in the `ErrorSchemaBuilder` back to the `initialSchema` if provided, otherwise an empty set.
   *
   * @param [initialSchema] - The optional set of initial errors, that will be cloned into the class
   * @returns - The `ErrorSchemaBuilder` object for chaining purposes
   */
  resetAllErrors(t) {
    return this.errorSchema = t ? kd(t) : {}, this;
  }
  /** Adds the `errorOrList` to the list of errors in the `ErrorSchema` at either the root level or the location within
   * the schema described by the `pathOfError`. For more information about how to specify the path see the
   * [eslint lodash plugin docs](https://github.com/wix/eslint-plugin-lodash/blob/master/docs/rules/path-style.md).
   *
   * @param errorOrList - The error or list of errors to add into the `ErrorSchema`
   * @param [pathOfError] - The optional path into the `ErrorSchema` at which to add the error(s)
   * @returns - The `ErrorSchemaBuilder` object for chaining purposes
   */
  addErrors(t, i) {
    const o = this.getOrCreateErrorBlock(i);
    let a = re(o, $t);
    return Array.isArray(a) || (a = [], o[$t] = a), Array.isArray(t) ? Be(o, $t, [.../* @__PURE__ */ new Set([...a, ...t])]) : Be(o, $t, [.../* @__PURE__ */ new Set([...a, t])]), this;
  }
  /** Sets/replaces the `errorOrList` as the error(s) in the `ErrorSchema` at either the root level or the location
   * within the schema described by the `pathOfError`. For more information about how to specify the path see the
   * [eslint lodash plugin docs](https://github.com/wix/eslint-plugin-lodash/blob/master/docs/rules/path-style.md).
   *
   * @param errorOrList - The error or list of errors to set into the `ErrorSchema`
   * @param [pathOfError] - The optional path into the `ErrorSchema` at which to set the error(s)
   * @returns - The `ErrorSchemaBuilder` object for chaining purposes
   */
  setErrors(t, i) {
    const o = this.getOrCreateErrorBlock(i), a = Array.isArray(t) ? [.../* @__PURE__ */ new Set([...t])] : [t];
    return Be(o, $t, a), this;
  }
  /** Clears the error(s) in the `ErrorSchema` at either the root level or the location within the schema described by
   * the `pathOfError`. For more information about how to specify the path see the
   * [eslint lodash plugin docs](https://github.com/wix/eslint-plugin-lodash/blob/master/docs/rules/path-style.md).
   *
   * @param [pathOfError] - The optional path into the `ErrorSchema` at which to clear the error(s)
   * @returns - The `ErrorSchemaBuilder` object for chaining purposes
   */
  clearErrors(t) {
    const i = this.getOrCreateErrorBlock(t);
    return Be(i, $t, []), this;
  }
}
function K0(e, t, i) {
  for (var o = -1, a = t.length, l = {}; ++o < a; ) {
    var c = t[o], f = Gl(e, c);
    i(f, c) && cd(l, wo(c, e), f);
  }
  return l;
}
function $T(e, t) {
  if (e == null)
    return {};
  var i = So(gd(e), function(o) {
    return [o];
  });
  return t = dd(t), K0(e, i, function(o, a) {
    return t(o, a[0]);
  });
}
var OT = 200;
function PT(e, t, i, o) {
  var a = -1, l = md, c = !0, f = e.length, d = [], m = t.length;
  if (!f)
    return d;
  t.length >= OT && (l = As, c = !1, t = new mi(t));
  e:
    for (; ++a < f; ) {
      var y = e[a], h = y;
      if (y = y !== 0 ? y : 0, c && h === h) {
        for (var S = m; S--; )
          if (t[S] === h)
            continue e;
        d.push(y);
      } else l(t, h, o) || d.push(y);
    }
  return d;
}
var CT = Ql(function(e, t) {
  return bs(e) ? PT(e, Gs(t, 1, bs, !0)) : [];
});
function ug(e, t) {
  const i = zr(e), o = zr(t);
  if (e === t || !i && !o)
    return [];
  if (i && !o)
    return vn(e);
  if (!i && o)
    return vn(t);
  {
    const a = vn($T(e, (c, f) => !Ge(c, re(t, f)))), l = CT(vn(t), vn(e));
    return [...a, ...l];
  }
}
function kT(e, t, i = [1900, (/* @__PURE__ */ new Date()).getFullYear() + 2], o = "YMD") {
  const { day: a, month: l, year: c, hour: f, minute: d, second: m } = e, y = { type: "day", range: [1, 31], value: a }, h = { type: "month", range: [1, 12], value: l }, S = { type: "year", range: i, value: c }, $ = [];
  switch (o) {
    case "MDY":
      $.push(h, y, S);
      break;
    case "DMY":
      $.push(y, h, S);
      break;
    case "YMD":
    default:
      $.push(S, h, y);
  }
  return t && $.push({ type: "hour", range: [0, 23], value: f }, { type: "minute", range: [0, 59], value: d }, { type: "second", range: [0, 59], value: m }), $;
}
function TT(e) {
  const t = {};
  return e.multipleOf && (t.step = e.multipleOf), (e.minimum || e.minimum === 0) && (t.min = e.minimum), (e.maximum || e.maximum === 0) && (t.max = e.maximum), t;
}
function NT(e, t, i = {}, o = !0) {
  const a = {
    type: t || "text",
    ...TT(e)
  };
  return i.inputType ? a.type = i.inputType : t || (e.type === "number" ? (a.type = "number", o && a.step === void 0 && (a.step = "any")) : e.type === "integer" && (a.type = "number", a.step === void 0 && (a.step = 1))), i.autocomplete && (a.autoComplete = i.autocomplete), i.accept && (a.accept = i.accept), a;
}
const cg = {
  props: {
    disabled: !1
  },
  submitText: "Submit",
  norender: !1
};
function IT(e = {}) {
  const t = Ee(e);
  if (t && t[jl]) {
    const i = t[jl];
    return { ...cg, ...i };
  }
  return cg;
}
function ke(e, t, i = {}) {
  const { templates: o } = t;
  if (e === "ButtonTemplates")
    return o[e];
  if (Object.hasOwn(i, e) && typeof i[e] == "string" && Object.hasOwn(o, i[e])) {
    const a = i[e];
    return o[a];
  }
  return (
    // Evaluating uiOptions[name] results in TS2590: Expression produces a union type that is too complex to represent
    // To avoid that, we cast uiOptions to `any` before accessing the name field
    i[e] || o[e]
  );
}
var jT = 0;
function W0(e) {
  var t = ++jT;
  return ad(e) + t;
}
var fg = { env: { NODE_ENV: "production" } };
function Td() {
  if (typeof fg > "u" || re(fg, "env.NODE_ENV") !== "test")
    return {};
  const e = /* @__PURE__ */ new Map();
  return new Proxy({}, {
    get(t, i) {
      return e.has(i) || e.set(i, W0("test-id-")), e.get(i);
    }
  });
}
var H0 = { exports: {} }, Ue = {};
/**
 * @license React
 * react-is.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
var dg;
function AT() {
  if (dg) return Ue;
  dg = 1;
  var e = Symbol.for("react.element"), t = Symbol.for("react.portal"), i = Symbol.for("react.fragment"), o = Symbol.for("react.strict_mode"), a = Symbol.for("react.profiler"), l = Symbol.for("react.provider"), c = Symbol.for("react.context"), f = Symbol.for("react.server_context"), d = Symbol.for("react.forward_ref"), m = Symbol.for("react.suspense"), y = Symbol.for("react.suspense_list"), h = Symbol.for("react.memo"), S = Symbol.for("react.lazy"), $ = Symbol.for("react.offscreen"), v;
  v = Symbol.for("react.module.reference");
  function w(_) {
    if (typeof _ == "object" && _ !== null) {
      var E = _.$$typeof;
      switch (E) {
        case e:
          switch (_ = _.type, _) {
            case i:
            case a:
            case o:
            case m:
            case y:
              return _;
            default:
              switch (_ = _ && _.$$typeof, _) {
                case f:
                case c:
                case d:
                case S:
                case h:
                case l:
                  return _;
                default:
                  return E;
              }
          }
        case t:
          return E;
      }
    }
  }
  return Ue.ContextConsumer = c, Ue.ContextProvider = l, Ue.Element = e, Ue.ForwardRef = d, Ue.Fragment = i, Ue.Lazy = S, Ue.Memo = h, Ue.Portal = t, Ue.Profiler = a, Ue.StrictMode = o, Ue.Suspense = m, Ue.SuspenseList = y, Ue.isAsyncMode = function() {
    return !1;
  }, Ue.isConcurrentMode = function() {
    return !1;
  }, Ue.isContextConsumer = function(_) {
    return w(_) === c;
  }, Ue.isContextProvider = function(_) {
    return w(_) === l;
  }, Ue.isElement = function(_) {
    return typeof _ == "object" && _ !== null && _.$$typeof === e;
  }, Ue.isForwardRef = function(_) {
    return w(_) === d;
  }, Ue.isFragment = function(_) {
    return w(_) === i;
  }, Ue.isLazy = function(_) {
    return w(_) === S;
  }, Ue.isMemo = function(_) {
    return w(_) === h;
  }, Ue.isPortal = function(_) {
    return w(_) === t;
  }, Ue.isProfiler = function(_) {
    return w(_) === a;
  }, Ue.isStrictMode = function(_) {
    return w(_) === o;
  }, Ue.isSuspense = function(_) {
    return w(_) === m;
  }, Ue.isSuspenseList = function(_) {
    return w(_) === y;
  }, Ue.isValidElementType = function(_) {
    return typeof _ == "string" || typeof _ == "function" || _ === i || _ === a || _ === o || _ === m || _ === y || _ === $ || typeof _ == "object" && _ !== null && (_.$$typeof === S || _.$$typeof === h || _.$$typeof === l || _.$$typeof === c || _.$$typeof === d || _.$$typeof === v || _.getModuleId !== void 0);
  }, Ue.typeOf = w, Ue;
}
H0.exports = AT();
var xT = H0.exports;
const pg = /* @__PURE__ */ zs(xT), ff = {
  boolean: {
    checkbox: "CheckboxWidget",
    radio: "RadioWidget",
    select: "SelectWidget",
    hidden: "HiddenWidget"
  },
  string: {
    text: "TextWidget",
    password: "PasswordWidget",
    email: "EmailWidget",
    hostname: "TextWidget",
    ipv4: "TextWidget",
    ipv6: "TextWidget",
    uri: "URLWidget",
    "data-url": "FileWidget",
    radio: "RadioWidget",
    select: "SelectWidget",
    textarea: "TextareaWidget",
    hidden: "HiddenWidget",
    date: "DateWidget",
    datetime: "DateTimeWidget",
    "date-time": "DateTimeWidget",
    "alt-date": "AltDateWidget",
    "alt-datetime": "AltDateTimeWidget",
    time: "TimeWidget",
    color: "ColorWidget",
    file: "FileWidget"
  },
  number: {
    text: "TextWidget",
    select: "SelectWidget",
    updown: "UpDownWidget",
    range: "RangeWidget",
    radio: "RadioWidget",
    hidden: "HiddenWidget"
  },
  integer: {
    text: "TextWidget",
    select: "SelectWidget",
    updown: "UpDownWidget",
    range: "RangeWidget",
    radio: "RadioWidget",
    hidden: "HiddenWidget"
  },
  array: {
    select: "SelectWidget",
    checkboxes: "CheckboxesWidget",
    files: "FileWidget",
    hidden: "HiddenWidget"
  }
};
function bT(e) {
  let t = re(e, "MergedWidget");
  if (!t) {
    const i = e.defaultProps && e.defaultProps.options || {};
    t = ({ options: o, ...a }) => D.jsx(e, { options: { ...i, ...o }, ...a }), Be(e, "MergedWidget", t);
  }
  return t;
}
function Vn(e, t, i = {}) {
  const o = En(e);
  if (typeof t == "function" || t && pg.isForwardRef(fe.createElement(t)) || pg.isMemo(t))
    return bT(t);
  if (typeof t != "string")
    throw new Error(`Unsupported widget definition: ${typeof t} in schema: ${JSON.stringify(e)}`);
  if (t in i) {
    const a = i[t];
    return Vn(e, a, i);
  }
  if (typeof o == "string") {
    if (!(o in ff))
      throw new Error(`No widget for type '${o}' in schema: ${JSON.stringify(e)}`);
    if (t in ff[o]) {
      const a = i[ff[o][t]];
      return Vn(e, a, i);
    }
  }
  throw new Error(`No widget '${t}' for type '${o}' in schema: ${JSON.stringify(e)}`);
}
function FT(e) {
  let t = 0;
  for (let i = 0; i < e.length; i += 1) {
    const o = e.charCodeAt(i);
    t = (t << 5) - t + o, t = t & t;
  }
  return t.toString(16);
}
function RT(e) {
  const t = /* @__PURE__ */ new Set();
  return JSON.stringify(e, (i, o) => (t.add(i), o)), JSON.stringify(e, Array.from(t).sort());
}
function Dn(e) {
  return FT(RT(e));
}
function DT(e) {
  return Dn(e);
}
function MT(e, t, i = {}) {
  try {
    return Vn(e, t, i), !0;
  } catch (o) {
    const a = o;
    if (a.message && (a.message.startsWith("No widget") || a.message.startsWith("Unsupported widget")))
      return !1;
    throw o;
  }
}
function Oi(e, t) {
  return `${Vr(e) ? e : e[Ke]}__${t}`;
}
function Ys(e) {
  return Oi(e, "description");
}
function q0(e) {
  return Oi(e, "error");
}
function Mf(e) {
  return Oi(e, "examples");
}
function G0(e) {
  return Oi(e, "help");
}
function Nd(e) {
  return Oi(e, "title");
}
function Pi(e, t = !1) {
  const i = t ? ` ${Mf(e)}` : "";
  return `${q0(e)} ${Ys(e)} ${G0(e)}${i}`;
}
function Y0(e, t) {
  return `${e}-${t}`;
}
function pi(e, t) {
  return Oi(e, t);
}
function df(e, t) {
  return Oi(e, `optional${t}`);
}
function $o(e) {
  return !Rl(e) && (!Fe(e) || Array.isArray(e) || !dt(e));
}
function LT(e, t) {
  const { rootSchema: i, schemaUtils: o } = e;
  if (xs(t, i))
    return !0;
  if (Ze in i) {
    const a = o.retrieveSchema(i);
    return xs(t, a);
  }
  return !1;
}
function UT(e, t, i) {
  return t ? i : e;
}
function zT(e) {
  return e ? new Date(e).toJSON() : void 0;
}
function Id(e, t, i) {
  const o = [S1];
  return Ae(e, vy) && o.unshift(vy), re(e, [...o, t], i);
}
function VT(e, t) {
  if (!Array.isArray(t))
    return e;
  const i = (y) => y.reduce((h, S) => (h[S] = !0, h), {}), o = (y) => y.length > 1 ? `properties '${y.join("', '")}'` : `property '${y[0]}'`, a = i(e), l = t.filter((y) => y === "*" || a[y]), c = i(l), f = e.filter((y) => !c[y]), d = l.indexOf("*");
  if (d === -1) {
    if (f.length)
      throw new Error(`uiSchema order list does not contain ${o(f)}`);
    return l;
  }
  if (d !== l.lastIndexOf("*"))
    throw new Error("uiSchema order list contains more than one wildcard item");
  const m = [...l];
  return m.splice(d, 1, ...f), m;
}
function pf(e, t = !0) {
  if (!e)
    return {
      year: -1,
      month: -1,
      day: -1,
      hour: t ? -1 : 0,
      minute: t ? -1 : 0,
      second: t ? -1 : 0
    };
  const i = new Date(e);
  if (Number.isNaN(i.getTime()))
    throw new Error("Unable to parse date " + e);
  return {
    year: i.getUTCFullYear(),
    month: i.getUTCMonth() + 1,
    // oh you, javascript.
    day: i.getUTCDate(),
    hour: t ? i.getUTCHours() : 0,
    minute: t ? i.getUTCMinutes() : 0,
    second: t ? i.getUTCSeconds() : 0
  };
}
function $l(e) {
  if (e.const || e.enum && e.enum.length === 1 && e.enum[0] === !0)
    return !0;
  if (e.anyOf && e.anyOf.length === 1)
    return $l(e.anyOf[0]);
  if (e.oneOf && e.oneOf.length === 1)
    return $l(e.oneOf[0]);
  if (e.allOf) {
    const t = (i) => $l(i);
    return e.allOf.some(t);
  }
  return !1;
}
function Q0(e, t, i, o = "customDeep") {
  if (o === "always")
    return !0;
  if (o === "shallow") {
    const { props: c, state: f } = e;
    return !lg(c, t) || !lg(f, i);
  }
  const { props: a, state: l } = e;
  return !Ge(a, t) || !Ge(l, i);
}
function hg(e) {
  const t = e0(e.map((i) => Fe(i) ? En(i) : void 0).flat().filter((i) => i !== void 0));
  return t.length === 1 ? t[0] : t;
}
function Qs(e, t, i, o) {
  const { enableOptionalDataFieldForType: a = [] } = Ee(o, e.globalUiOptions);
  let l;
  return be in t && Array.isArray(t[be]) ? l = hg(t[be]) : Ne in t && Array.isArray(t[Ne]) ? l = hg(t[Ne]) : l = En(t), !LT(e, t) && !i && !!l && !Array.isArray(l) && !!a.find((c) => c === l);
}
function mg(e, t = !0) {
  const { year: i, month: o, day: a, hour: l = 0, minute: c = 0, second: f = 0 } = e, d = Date.UTC(i, o - 1, a, l, c, f), m = new Date(d).toJSON();
  return t ? m : m.slice(0, 10);
}
function jd(e, t = []) {
  if (!e)
    return [];
  let i = [];
  return $t in e && (i = i.concat(e[$t].map((o) => {
    const a = `.${t.join(".")}`;
    return {
      property: a,
      message: o,
      stack: `${a} ${o}`
    };
  }))), Object.keys(e).reduce((o, a) => {
    if (a !== $t) {
      const l = e[a];
      zr(l) && (o = o.concat(jd(l, [...t, a])));
    }
    return o;
  }, i);
}
function J0(e) {
  return yt(e) ? So(e, $i) : Hs(e) ? [e] : hd(xv(ad(e)));
}
function BT(e) {
  const t = new B0();
  return e.length && e.forEach((i) => {
    const { property: o, message: a } = i, l = o === "." ? [] : J0(o);
    l.length > 0 && l[0] === "" && l.splice(0, 1), a && t.addErrors(a, l);
  }), t.ErrorSchema;
}
function ln(e, t, i, o) {
  const a = Array.isArray(i) ? i : i == null ? void 0 : i.path, l = e === "" ? [] : [e], c = a ? a.concat(...l) : l, f = [t.idPrefix, ...c].join(t.idSeparator);
  let d;
  return t.nameGenerator && c.length > 0 && (d = t.nameGenerator(c, t.idPrefix, o)), { path: c, [Ke]: f, ...d !== void 0 && { name: d } };
}
function X0(e) {
  return Object.keys(e).reduce((t, i) => {
    if (i === "addError")
      return t;
    {
      const o = e[i];
      return zr(o) ? {
        ...t,
        [i]: X0(o)
      } : { ...t, [i]: o };
    }
  }, {});
}
function KT(e) {
  return Object.values(e).every((t) => t !== -1);
}
function WT(e) {
  const { className: t = "form-control", type: i, range: o, value: a, select: l, rootId: c, name: f, disabled: d, readonly: m, autofocus: y, registry: h, onBlur: S, onFocus: $ } = e, v = `${c}_${i}`, { SelectWidget: w } = h.widgets, _ = fe.useCallback((E) => l(i, E), [l, i]);
  return D.jsx(w, { schema: { type: "integer" }, id: v, name: f, className: t, options: { enumOptions: V0(o[0], o[1]) }, placeholder: i, value: a, disabled: d, readonly: m, autofocus: y, onChange: _, onBlur: S, onFocus: $, registry: h, label: "", "aria-describedby": Pi(c) });
}
function HT(e) {
  const { time: t = !1, disabled: i = !1, readonly: o = !1, options: a, onChange: l, value: c } = e, [f, d] = fe.useState(pf(c, t));
  fe.useEffect(() => {
    d(pf(c, t));
  }, [t, c]);
  const m = fe.useCallback(($, v) => {
    const w = {
      ...f,
      [$]: typeof v > "u" ? -1 : v
    };
    KT(w) ? l(mg(w, t)) : d(w);
  }, [f, l, t]), y = fe.useCallback(($) => {
    $.preventDefault(), !(i || o) && l(void 0);
  }, [i, o, l]), h = fe.useCallback(($) => {
    if ($.preventDefault(), i || o)
      return;
    const v = pf((/* @__PURE__ */ new Date()).toJSON(), t);
    l(mg(v, t));
  }, [i, o, t, l]);
  return { elements: fe.useMemo(() => kT(f, t, a.yearsRange, a.format), [f, t, a.yearsRange, a.format]), handleChange: m, handleClear: y, handleSetNow: h };
}
function Ci(e) {
  const t = fe.useRef(e);
  return xs(e, t.current) || (t.current = e), t.current;
}
function qT(e, t) {
  return e.replace(";base64", `;name=${encodeURIComponent(t)};base64`);
}
function GT(e) {
  const { name: t, size: i, type: o } = e;
  return new Promise((a, l) => {
    const c = new window.FileReader();
    c.onerror = l, c.onload = (f) => {
      var d;
      typeof ((d = f.target) === null || d === void 0 ? void 0 : d.result) == "string" ? a({
        dataURL: qT(f.target.result, t),
        name: t,
        size: i,
        type: o
      }) : a({
        dataURL: null,
        name: t,
        size: i,
        type: o
      });
    }, c.readAsDataURL(e);
  });
}
function YT(e) {
  return Promise.all(Array.from(e).map(GT));
}
function yg(e) {
  return e.reduce((t, i) => {
    if (!i)
      return t;
    try {
      const { blob: o, name: a } = hT(i);
      return [
        ...t,
        {
          dataURL: i,
          name: a,
          size: o.size,
          type: o.type
        }
      ];
    } catch {
      return t;
    }
  }, []);
}
function QT(e, t, i = !1) {
  const o = fe.useMemo(() => i && e ? Array.isArray(e) ? e : [e] : [], [e, i]), a = fe.useMemo(() => Array.isArray(e) ? yg(e) : yg([e || ""]), [e]), l = fe.useCallback((f) => {
    YT(f).then((d) => {
      const m = d.map((y) => y.dataURL || null);
      t(i ? o.concat(...m) : m[0]);
    });
  }, [o, i, t]), c = fe.useCallback((f) => {
    if (i) {
      const d = o.filter((m, y) => y !== f);
      t(d);
    } else
      t(void 0);
  }, [o, i, t]);
  return { filesInfo: a, handleChange: l, handleRemove: c };
}
function JT(e) {
  if (!e)
    return "";
  const t = new Date(e), i = Ar(t.getFullYear(), 4), o = Ar(t.getMonth() + 1, 2), a = Ar(t.getDate(), 2), l = Ar(t.getHours(), 2), c = Ar(t.getMinutes(), 2), f = Ar(t.getSeconds(), 2), d = Ar(t.getMilliseconds(), 3);
  return `${i}-${o}-${a}T${l}:${c}:${f}.${d}`;
}
function Ol(e, t, i = !1) {
  if (!t)
    return e;
  const { errors: o, errorSchema: a } = e;
  let l = jd(t), c = t;
  return dt(a) || (c = Ls(a, t, i ? "preventDuplicates" : !0), l = [...o].concat(l)), { errorSchema: c, errors: l };
}
function XT(e) {
  for (const t in e) {
    const i = e, o = i[t];
    t === Ze && typeof o == "string" && o.startsWith("#") ? i[t] = _v + o : i[t] = Ad(o);
  }
  return e;
}
function ZT(e) {
  for (let t = 0; t < e.length; t++)
    e[t] = Ad(e[t]);
  return e;
}
function Ad(e) {
  return Array.isArray(e) ? ZT([...e]) : Fe(e) ? XT({ ...e }) : e;
}
var Le;
(function(e) {
  e.ArrayItemTitle = "Item", e.MissingItems = "Missing items definition", e.EmptyArray = "No items yet. Use the button below to add some.", e.YesLabel = "Yes", e.NoLabel = "No", e.CloseLabel = "Close", e.ErrorsLabel = "Errors", e.NewStringDefault = "New Value", e.AddButton = "Add", e.AddItemButton = "Add Item", e.CopyButton = "Copy", e.MoveDownButton = "Move down", e.MoveUpButton = "Move up", e.RemoveButton = "Remove", e.NowLabel = "Now", e.ClearLabel = "Clear", e.AriaDateLabel = "Select a date", e.PreviewLabel = "Preview", e.DecrementAriaLabel = "Decrease value by 1", e.IncrementAriaLabel = "Increase value by 1", e.OptionalObjectAdd = "Add data for optional field", e.OptionalObjectRemove = "Remove data for optional field", e.OptionalObjectEmptyMsg = "No data for optional field", e.Type = "Type", e.Value = "Value", e.UnknownFieldType = "Unknown field type %1", e.OptionPrefix = "Option %1", e.TitleOptionPrefix = "%1 option %2", e.KeyLabel = "%1 Key", e.InvalidObjectField = 'Invalid "%1" object field configuration: _%2_.', e.UnsupportedField = "Unsupported field schema.", e.UnsupportedFieldWithId = "Unsupported field schema for field `%1`.", e.UnsupportedFieldWithReason = "Unsupported field schema: _%1_.", e.UnsupportedFieldWithIdAndReason = "Unsupported field schema for field `%1`: _%2_.", e.FilesInfo = "**%1** (%2, %3 bytes)";
})(Le || (Le = {}));
function eN(e, t) {
  var i = yt(e) ? fd : F0;
  return i(e, Rv(t));
}
function tN(e, t) {
  return K0(e, t, function(i, o) {
    return Kv(e, o);
  });
}
var Z0 = p0(function(e, t) {
  return e == null ? {} : tN(e, t);
});
function nN(e, t) {
  return e == null ? !0 : d0(e, t);
}
function Lf() {
  return W0("rjsf-array-item-");
}
function gg(e) {
  return Array.isArray(e) ? e.map((t) => ({
    key: Lf(),
    item: t
  })) : [];
}
function e_(e) {
  return Array.isArray(e) ? e.map((t) => t.item) : [];
}
function rN(e) {
  return Array.isArray(e.type) ? !e.type.includes("null") : e.type !== "null";
}
function t_(e, t, i, o) {
  let { addable: a } = Ee(o, e.globalUiOptions);
  return a !== !1 && (t.maxItems !== void 0 ? a = i.length < t.maxItems : a = !0), a;
}
function n_(e, t, i, o) {
  if (typeof e.items == "function")
    try {
      return e.items(t, i, o);
    } catch (a) {
      console.error(`Error executing dynamic uiSchema.items function for item at index ${i}:`, a);
      return;
    }
  else
    return e.items;
}
function iN(e, t) {
  const { schemaUtils: i, globalFormOptions: o } = e;
  let a = t.items;
  return o.useFallbackUiForUnsupportedType && !a ? a = {} : $d(t) && m1(t) && (a = t.additionalItems), i.getDefaultFormState(a);
}
function oN(e) {
  const { schema: t, fieldPathId: i, uiSchema: o, formData: a = [], disabled: l = !1, readonly: c = !1, autofocus: f = !1, required: d = !1, placeholder: m, onBlur: y, onFocus: h, registry: S, rawErrors: $, name: v, onSelectChange: w } = e, { widgets: _, schemaUtils: E, globalFormOptions: k, globalUiOptions: j } = S, T = E.retrieveSchema(t.items, a), N = yo(T, o), { widget: x = "select", title: F, ...V } = Ee(o, j), U = Vn(t, x, _), G = F ?? t.title ?? v, Q = E.getDisplayLabel(t, o, j), H = Ci(ln("", k, i, !0));
  return D.jsx(U, { id: H[Ke], name: v, multiple: !0, onChange: w, onBlur: y, onFocus: h, options: { ...V, enumOptions: N }, schema: t, uiSchema: o, registry: S, value: a, disabled: l, readonly: c, required: d, label: G, hideLabel: !Q, placeholder: m, autofocus: f, rawErrors: $, htmlName: H.name });
}
function sN(e) {
  const { schema: t, fieldPathId: i, uiSchema: o, disabled: a = !1, readonly: l = !1, autofocus: c = !1, required: f = !1, hideError: d, placeholder: m, onBlur: y, onFocus: h, formData: S = [], registry: $, rawErrors: v, name: w, onSelectChange: _ } = e, { widgets: E, schemaUtils: k, globalFormOptions: j, globalUiOptions: T } = $, { widget: N, title: x, ...F } = Ee(o, T), V = Vn(t, N, E), U = x ?? t.title ?? w, G = k.getDisplayLabel(t, o, T), Q = Ci(ln("", j, i, !0));
  return D.jsx(V, { id: Q[Ke], name: w, multiple: !0, onChange: _, onBlur: y, onFocus: h, options: F, schema: t, uiSchema: o, registry: $, value: S, disabled: a, readonly: l, hideError: d, required: f, label: U, hideLabel: !G, placeholder: m, autofocus: c, rawErrors: v, htmlName: Q.name });
}
function aN(e) {
  const { schema: t, uiSchema: i, fieldPathId: o, name: a, disabled: l = !1, readonly: c = !1, autofocus: f = !1, required: d = !1, onBlur: m, onFocus: y, registry: h, formData: S = [], rawErrors: $, onSelectChange: v } = e, { widgets: w, schemaUtils: _, globalFormOptions: E, globalUiOptions: k } = h, { widget: j = "files", title: T, ...N } = Ee(i, k), x = Vn(t, j, w), F = T ?? t.title ?? a, V = _.getDisplayLabel(t, i, k), U = Ci(ln("", E, o, !0));
  return D.jsx(x, { options: N, id: U[Ke], name: a, multiple: !0, onChange: v, onBlur: m, onFocus: y, schema: t, uiSchema: i, value: S, disabled: l, readonly: c, required: d, registry: h, autofocus: f, rawErrors: $, label: F, hideLabel: !V, htmlName: U.name });
}
function r_(e) {
  const { itemKey: t, index: i, name: o, disabled: a, hideError: l, readonly: c, registry: f, uiOptions: d, parentUiSchema: m, canAdd: y, canRemove: h = !0, canMoveUp: S, canMoveDown: $, itemSchema: v, itemData: w, itemUiSchema: _, itemFieldPathId: E, itemErrorSchema: k, autofocus: j, onBlur: T, onFocus: N, onChange: x, rawErrors: F, totalItems: V, title: U, handleAddItem: G, handleCopyItem: Q, handleRemoveItem: H, handleReorderItems: q } = e, { schemaUtils: le, fields: { ArraySchemaField: ie, SchemaField: ne }, globalUiOptions: pe } = f, Z = Ci(E), ae = ie || ne, z = ke("ArrayFieldItemTemplate", f, d), P = le.getDisplayLabel(v, _, pe), { description: b } = Ee(_), R = !!b || !!v.description, { orderable: C = !0, removable: I = !0, copyable: B = !1 } = d, X = {
    moveUp: C && S,
    moveDown: C && $,
    copy: B && y,
    remove: I && h,
    toolbar: !1
  };
  X.toolbar = Object.keys(X).some((ze) => X[ze]);
  const J = fe.useCallback((ze) => {
    G(ze, i + 1);
  }, [G, i]), se = fe.useCallback((ze) => {
    Q(ze, i);
  }, [Q, i]), ce = fe.useCallback((ze) => {
    H(ze, i);
  }, [H, i]), $e = fe.useCallback((ze) => {
    q(ze, i, i - 1);
  }, [q, i]), nt = fe.useCallback((ze) => {
    q(ze, i, i + 1);
  }, [q, i]), ot = {
    children: D.jsx(ae, { name: o, title: U, index: i, schema: v, uiSchema: _, formData: w, errorSchema: k, fieldPathId: Z, required: rN(v), onChange: x, onBlur: T, onFocus: N, registry: f, disabled: a, readonly: c, hideError: l, autofocus: j, rawErrors: F }),
    buttonsProps: {
      fieldPathId: Z,
      disabled: a,
      readonly: c,
      canAdd: y,
      hasCopy: X.copy,
      hasMoveUp: X.moveUp,
      hasMoveDown: X.moveDown,
      hasRemove: X.remove,
      index: i,
      totalItems: V,
      onAddItem: J,
      onCopyItem: se,
      onRemoveItem: ce,
      onMoveUpItem: $e,
      onMoveDownItem: nt,
      registry: f,
      schema: v,
      uiSchema: _
    },
    itemKey: t,
    className: "rjsf-array-item",
    disabled: a,
    hasToolbar: X.toolbar,
    index: i,
    totalItems: V,
    readonly: c,
    registry: f,
    schema: v,
    uiSchema: _,
    parentUiSchema: m,
    displayLabel: P,
    hasDescription: R
  };
  return D.jsx(z, { ...ot });
}
function lN(e) {
  const { schema: t, uiSchema: i = {}, errorSchema: o, fieldPathId: a, formData: l, name: c, title: f, disabled: d = !1, readonly: m = !1, autofocus: y = !1, required: h = !1, hideError: S = !1, registry: $, onBlur: v, onFocus: w, rawErrors: _, onChange: E, keyedFormData: k, handleAddItem: j, handleCopyItem: T, handleRemoveItem: N, handleReorderItems: x } = e, F = t.title || f || c, { schemaUtils: V, fields: U, formContext: G, globalFormOptions: Q, globalUiOptions: H } = $, { OptionalDataControlsField: q } = U, le = Ee(i, H), ie = Fe(t.items) ? t.items : {}, ne = V.retrieveSchema(ie), pe = e_(k), Z = Qs($, t, h, i), ae = $o(l), z = t_($, t, pe, i) && (!Z || ae), P = ae ? k : [], b = Z ? " rjsf-optional-array-field" : "", R = e.childFieldPathId ?? a, C = Z ? D.jsx(q, { ...e, fieldPathId: R }) : void 0, I = {
    canAdd: z,
    items: P.map((X, J) => {
      const { key: se, item: ce } = X, $e = ce, nt = V.retrieveSchema(ie, $e), ot = o ? o[J] : void 0, ze = ln(J, Q, R), Rt = n_(i, ce, J, G), et = {
        itemKey: se,
        index: J,
        name: c && `${c}-${J}`,
        registry: $,
        uiOptions: le,
        hideError: S,
        readonly: m,
        disabled: d,
        required: h,
        title: F ? `${F}-${J + 1}` : void 0,
        canAdd: z,
        canMoveUp: J > 0,
        canMoveDown: J < pe.length - 1,
        itemSchema: nt,
        itemFieldPathId: ze,
        itemErrorSchema: ot,
        itemData: $e,
        itemUiSchema: Rt,
        autofocus: y && J === 0,
        onBlur: v,
        onFocus: w,
        rawErrors: _,
        totalItems: k.length,
        handleAddItem: j,
        handleCopyItem: T,
        handleRemoveItem: N,
        handleReorderItems: x,
        onChange: E
      };
      return D.jsx(r_, { ...et }, se);
    }),
    className: `rjsf-field rjsf-field-array rjsf-field-array-of-${ne.type}${b}`,
    disabled: d,
    fieldPathId: a,
    uiSchema: i,
    onAddClick: j,
    readonly: m,
    required: h,
    schema: t,
    title: F,
    formData: pe,
    rawErrors: _,
    registry: $,
    optionalDataControl: C
  }, B = ke("ArrayFieldTemplate", $, le);
  return D.jsx(B, { ...I });
}
function uN(e) {
  const { schema: t, uiSchema: i = {}, formData: o, errorSchema: a, fieldPathId: l, name: c, title: f, disabled: d = !1, readonly: m = !1, autofocus: y = !1, required: h = !1, hideError: S = !1, registry: $, onBlur: v, onFocus: w, rawErrors: _, keyedFormData: E, onChange: k, handleAddItem: j, handleCopyItem: T, handleRemoveItem: N, handleReorderItems: x } = e;
  let { formData: F = [] } = e;
  const V = t.title || f || c, { schemaUtils: U, fields: G, formContext: Q, globalFormOptions: H, globalUiOptions: q } = $, le = Ee(i, q), { OptionalDataControlsField: ie } = G, ne = Qs($, t, h, i), pe = $o(o), ae = (Fe(t.items) ? t.items : []).map((J, se) => U.retrieveSchema(J, F[se])), z = Fe(t.additionalItems) ? U.retrieveSchema(t.additionalItems, o) : null, P = e.childFieldPathId ?? l;
  F.length < ae.length && (F = F.concat(new Array(ae.length - F.length)));
  const b = pe ? E : [], R = ne ? " rjsf-optional-array-field" : "", C = ne ? D.jsx(ie, { ...e, fieldPathId: P }) : void 0, I = t_($, t, F, i) && !!z && (!ne || pe), B = {
    canAdd: I,
    className: `rjsf-field rjsf-field-array rjsf-field-array-fixed-items${R}`,
    disabled: d,
    fieldPathId: l,
    formData: o,
    items: b.map((J, se) => {
      const { key: ce, item: $e } = J, nt = $e, ot = se >= ae.length, ze = (ot && Fe(t.additionalItems) ? U.retrieveSchema(t.additionalItems, nt) : ae[se]) || {}, Rt = ln(se, H, P);
      let et;
      ot ? et = i.additionalItems : Array.isArray(i.items) ? et = i.items[se] : et = n_(i, $e, se, Q);
      const Wt = a ? a[se] : void 0, Pt = {
        index: se,
        itemKey: ce,
        name: c && `${c}-${se}`,
        registry: $,
        uiOptions: le,
        hideError: S,
        readonly: m,
        disabled: d,
        required: h,
        title: V ? `${V}-${se + 1}` : void 0,
        canAdd: I,
        canRemove: ot,
        canMoveUp: se >= ae.length + 1,
        canMoveDown: ot && se < F.length - 1,
        itemSchema: ze,
        itemData: nt,
        itemUiSchema: et,
        itemFieldPathId: Rt,
        itemErrorSchema: Wt,
        autofocus: y && se === 0,
        onBlur: v,
        onFocus: w,
        rawErrors: _,
        totalItems: E.length,
        onChange: k,
        handleAddItem: j,
        handleCopyItem: T,
        handleRemoveItem: N,
        handleReorderItems: x
      };
      return D.jsx(r_, { ...Pt }, ce);
    }),
    onAddClick: j,
    readonly: m,
    required: h,
    registry: $,
    schema: t,
    uiSchema: i,
    title: V,
    errorSchema: a,
    rawErrors: _,
    optionalDataControl: C
  }, X = ke("ArrayFieldTemplate", $, le);
  return D.jsx(X, { ...B });
}
function cN(e = []) {
  const t = fe.useMemo(() => Dn(e), [e]), [i, o] = fe.useState(() => ({
    formDataHash: t,
    keyedFormData: gg(e)
  }));
  let { keyedFormData: a, formDataHash: l } = i;
  if (t !== l) {
    const f = Array.isArray(e) ? e : [], d = a || [];
    a = f.length === d.length ? d.map((m, y) => ({
      key: m.key,
      item: f[y]
    })) : gg(f), l = t, o({ formDataHash: l, keyedFormData: a });
  }
  const c = fe.useCallback((f) => {
    const d = e_(f), m = Dn(d);
    return o({ formDataHash: m, keyedFormData: f }), d;
  }, []);
  return { keyedFormData: a, updateKeyedFormData: c };
}
function fN(e) {
  const { schema: t, uiSchema: i, errorSchema: o, fieldPathId: a, registry: l, formData: c, onChange: f } = e, { globalFormOptions: d, schemaUtils: m, translateString: y } = l, { keyedFormData: h, updateKeyedFormData: S } = cN(c), $ = e.childFieldPathId ?? a, v = fe.useCallback((x, F) => {
    x && x.preventDefault();
    let V;
    if (o) {
      V = {};
      for (const Q in o) {
        const H = parseInt(Q);
        F === void 0 || H < F ? Be(V, [H], o[Q]) : H >= F && Be(V, [H + 1], o[Q]);
      }
    }
    const U = {
      key: Lf(),
      item: iN(l, t)
    }, G = [...h];
    F !== void 0 ? G.splice(F, 0, U) : G.push(U), f(S(G), $.path, V);
  }, [h, l, t, f, S, o, $]), w = fe.useCallback((x, F) => {
    x && x.preventDefault();
    let V;
    if (o) {
      V = {};
      for (const Q in o) {
        const H = parseInt(Q);
        H <= F ? Be(V, [H], o[Q]) : H > F && Be(V, [H + 1], o[Q]);
      }
    }
    const U = {
      key: Lf(),
      item: kd(h[F].item)
    }, G = [...h];
    F !== void 0 ? G.splice(F + 1, 0, U) : G.push(U), f(S(G), $.path, V);
  }, [h, f, S, o, $]), _ = fe.useCallback((x, F) => {
    x && x.preventDefault();
    let V;
    if (o) {
      V = {};
      for (const G in o) {
        const Q = parseInt(G);
        Q < F ? Be(V, [Q], o[G]) : Q > F && Be(V, [Q - 1], o[G]);
      }
    }
    const U = h.filter((G, Q) => Q !== F);
    f(S(U), $.path, V);
  }, [h, f, S, o, $]), E = fe.useCallback((x, F, V) => {
    x && (x.preventDefault(), x.currentTarget.blur());
    let U;
    if (o) {
      U = {};
      for (const H in o) {
        const q = parseInt(H);
        q == F ? Be(U, [V], o[F]) : q == V ? Be(U, [F], o[V]) : Be(U, [H], o[q]);
      }
    }
    function G() {
      const H = h.slice();
      return H.splice(F, 1), H.splice(V, 0, h[F]), H;
    }
    const Q = G();
    f(S(Q), $.path, U);
  }, [h, f, S, o, $]), k = fe.useCallback((x, F, V, U) => {
    f(
      // We need to treat undefined items as nulls to have validation.
      // See https://github.com/tdegrunt/jsonschema/issues/206
      x === void 0 ? null : x,
      F,
      V,
      U
    );
  }, [f]), j = fe.useCallback((x) => {
    f(x, $.path, void 0, $ == null ? void 0 : $[Ke]);
  }, [f, $]), T = {
    ...e,
    formData: c,
    fieldPathId: $,
    onSelectChange: j
  }, N = {
    ...e,
    handleAddItem: v,
    handleCopyItem: w,
    handleRemoveItem: _,
    handleReorderItems: E,
    keyedFormData: h,
    onChange: k
  };
  if (!(po in t)) {
    if (!d.useFallbackUiForUnsupportedType) {
      const F = Ee(i), V = ke("UnsupportedFieldTemplate", l, F);
      return D.jsx(V, { schema: t, fieldPathId: a, reason: y(Le.MissingItems), registry: l });
    }
    const x = { ...t, [po]: { type: void 0 } };
    T.schema = x, N.schema = x;
  }
  return m.isMultiSelect(T.schema) ? D.jsx(oN, { ...T }) : U0(i) ? D.jsx(sN, { ...T }) : $d(T.schema) ? D.jsx(uN, { ...N }) : m.isFilesArray(T.schema, i) ? D.jsx(aN, { ...T }) : D.jsx(lN, { ...N });
}
function dN(e) {
  const { schema: t, name: i, uiSchema: o, fieldPathId: a, formData: l, registry: c, required: f, disabled: d, readonly: m, hideError: y, autofocus: h, title: S, onChange: $, onFocus: v, onBlur: w, rawErrors: _ } = e, { title: E } = t, { widgets: k, translateString: j, globalUiOptions: T } = c, {
    widget: N = "checkbox",
    title: x,
    // Unlike the other fields, don't use `getDisplayLabel()` since it always returns false for the boolean type
    label: F = !0,
    enumNames: V,
    ...U
  } = Ee(o, T), G = Vn(t, N, k), Q = j(Le.YesLabel), H = j(Le.NoLabel);
  let q;
  const le = x ?? E ?? S ?? i;
  if (Array.isArray(t.oneOf))
    q = yo({
      oneOf: t.oneOf.map((ne) => {
        if (Fe(ne))
          return {
            ...ne,
            title: ne.title || (ne.const === !0 ? Q : H)
          };
      }).filter((ne) => ne)
      // cast away the error that typescript can't grok is fixed
    }, o);
  else {
    const ne = t.enum ?? [!0, !1];
    !V && ne.length === 2 && ne.every((pe) => typeof pe == "boolean") ? q = [
      {
        value: ne[0],
        label: ne[0] ? Q : H
      },
      {
        value: ne[1],
        label: ne[1] ? Q : H
      }
    ] : q = yo({ enum: ne }, o);
  }
  const ie = fe.useCallback((ne, pe, Z) => $(ne, a.path, pe, Z), [$, a]);
  return D.jsx(G, { options: { ...U, enumOptions: q }, schema: t, uiSchema: o, id: a.$id, name: i, onChange: ie, onFocus: v, onBlur: w, label: le, hideLabel: !F, value: l, required: f, disabled: d, readonly: m, hideError: y, registry: c, autofocus: h, rawErrors: _, htmlName: a.name });
}
function pN(e) {
  return {
    type: "string",
    enum: ["string", "number", "boolean", "object", "array"],
    default: "string",
    title: e
  };
}
function hN(e) {
  const t = typeof e;
  return t === "string" || t === "number" || t === "boolean" ? t : t === "object" ? Array.isArray(e) ? "array" : "object" : "string";
}
function mN(e, t) {
  switch (t) {
    case "string":
      return String(e);
    case "number": {
      const i = Number(e);
      return isNaN(i) ? 0 : i;
    }
    case "boolean":
      return !!e;
    default:
      return e;
  }
}
function yN(e) {
  const { id: t, formData: i, displayLabel: o = !0, schema: a, name: l, uiSchema: c, required: f, disabled: d = !1, readonly: m = !1, onBlur: y, onFocus: h, registry: S, fieldPathId: $, onChange: v, errorSchema: w } = e, { translateString: _, fields: E, globalFormOptions: k } = S, [j, T] = fe.useState(hN(i)), N = Ee(c), x = Ci(ln("__internal_type_selector", k, $)), F = _(Le.Type), V = fe.useMemo(() => pN(F), [F]), U = (H) => {
    H != null && (T(H), v(mN(i, H), $.path, w, t));
  };
  if (!k.useFallbackUiForUnsupportedType) {
    const { reason: H = _(Le.UnknownFieldType, [String(a.type)]) } = e, q = ke("UnsupportedFieldTemplate", S, N);
    return D.jsx(q, { schema: a, fieldPathId: $, reason: H, registry: S });
  }
  const G = ke("FallbackFieldTemplate", S, N), { SchemaField: Q } = E;
  return D.jsx(G, { schema: a, registry: S, typeSelector: D.jsx(Q, { fieldPathId: x, name: `${l}__fallback_type`, schema: V, formData: j, onChange: U, onBlur: y, onFocus: h, registry: S, hideLabel: !o, disabled: d, readonly: m, required: f }, i ? Dn(i) : "__empty__"), schemaField: D.jsx(Q, { ...e, schema: {
    type: j,
    title: _(Le.Value),
    ...j === "object" && { additionalProperties: !0 }
  } }) });
}
function gN(e, t) {
  return So(t, function(i) {
    return e[i];
  });
}
function vN(e) {
  return e == null ? [] : gN(e, vn(e));
}
var _N = Math.max;
function SN(e, t, i, o) {
  e = Ei(e) ? e : vN(e), i = i ? Dv(i) : 0;
  var a = e.length;
  return i < 0 && (i = _N(a + i, 0)), Vr(e) ? i <= a && e.indexOf(t, i) > -1 : !!a && Xv(e, t, i) > -1;
}
var wN = Math.min;
function EN(e, t, i) {
  for (var o = md, a = e[0].length, l = e.length, c = l, f = Array(l), d = 1 / 0, m = []; c--; ) {
    var y = e[c];
    d = wN(y.length, d), f[c] = a >= 120 && y.length >= 120 ? new mi(c && y) : void 0;
  }
  y = e[0];
  var h = -1, S = f[0];
  e:
    for (; ++h < a && m.length < d; ) {
      var $ = y[h], v = $;
      if ($ = $ !== 0 ? $ : 0, !(S ? As(S, v) : o(m, v))) {
        for (c = l; --c; ) {
          var w = f[c];
          if (!(w ? As(w, v) : o(e[c], v)))
            continue e;
        }
        S && S.push(v), m.push($);
      }
    }
  return m;
}
function $N(e) {
  return bs(e) ? e : [];
}
var vg = Ql(function(e) {
  var t = So(e, $N);
  return t.length && t[0] === e[0] ? EN(t) : [];
});
function i_(e) {
  return e === void 0;
}
var Mn;
(function(e) {
  e.ROW = "ui:row", e.COLUMN = "ui:col", e.COLUMNS = "ui:columns", e.CONDITION = "ui:condition";
})(Mn || (Mn = {}));
var $s;
(function(e) {
  e.ALL = "all", e.SOME = "some", e.NONE = "none";
})($s || ($s = {}));
const ON = /^\$lookup=(.+)/, hf = "layoutGrid";
function _g(e, t) {
  return e ?? t;
}
function PN(e) {
  return /^\d+?$/.test(e);
}
const Mr = Td();
function CN(e, t, i, o, a) {
  const l = re(i, [Cf], {}), c = re(i, e), f = { ...re(c, [Rr], {}), ...t, ...l }, d = { ...c };
  dt(f) || Be(d, [Rr], f), dt(l) || Be(d, [Cf], l);
  let { readonly: m } = Ee(d);
  return (a === !0 || i_(m) && o === !0) && (m = !0, Ae(f, Jc) ? Be(d, [Rr, Jc], !0) : Be(d, `ui:${Jc}`, !0)), { fieldUiSchema: d, uiReadonly: m };
}
function kN(e, t, i = "$0m3tH1nG Un3xP3cT3d") {
  const o = bf([t]).sort(), a = bf([i]).sort();
  switch (e) {
    case $s.ALL:
      return xs(o, a);
    case $s.SOME:
      return vg(o, a).length > 0;
    case $s.NONE:
      return vg(o, a).length === 0;
    default:
      return !1;
  }
}
function Zl(e, t, i) {
  let o = {}, a = e[t];
  if (zr(a)) {
    const { children: l, className: c, ...f } = a;
    if (a = l, c) {
      const m = c.split(" ").map((y) => Id(i, y, y)).join(" ");
      o = { ...f, className: m };
    } else
      o = f;
  }
  if (!Array.isArray(a))
    throw new TypeError(`Expected array for "${t}" in ${JSON.stringify(e)}`);
  return { children: a, gridProps: o };
}
function Sg(e, t, i) {
  let o;
  if (PN(i) && e && (e == null ? void 0 : e.type) === "array" && Ae(e, po)) {
    const a = Number(i), l = e[po];
    Array.isArray(l) ? a > l.length ? o = f0(l) : o = l[a] : o = l, t = {
      [Ke]: t[Ke],
      path: [...t.path.slice(0, t.path.length - 1), a]
    };
  }
  return { rawSchema: o, fieldPathId: t };
}
function TN(e, t, i, o, a) {
  const { schemaUtils: l, globalFormOptions: c } = e;
  let f = i, d = a;
  const m = t.split("."), y = m.pop();
  let h = l.retrieveSchema(f, o), S = o, $ = h.readOnly;
  m.forEach((_) => {
    if (d = ln(_, c, d), Ae(h, Me))
      f = re(h, [Me, _], {});
    else if (h && (Ae(h, Ne) || Ae(h, be))) {
      const E = Ae(h, Ne) ? Ne : be, k = l.findSelectedOptionInXxxOf(h, _, E, S);
      f = re(k, [Me, _], {});
    } else {
      const E = Sg(h, d, _);
      f = E.rawSchema ?? {}, d = E.fieldPathId;
    }
    S = re(S, _, {}), h = l.retrieveSchema(f, S), $ = _g(h.readOnly, $);
  });
  let v, w = !1;
  if (dt(h) && (h = void 0), h && y) {
    if (h && (Ae(h, Ne) || Ae(h, be))) {
      const E = Ae(h, Ne) ? Ne : be;
      h = l.findSelectedOptionInXxxOf(h, y, E, S);
    }
    d = ln(y, c, d), w = h !== void 0 && Array.isArray(h.required) && SN(h.required, y);
    const _ = Sg(h, d, y);
    if (_.rawSchema ? (h = _.rawSchema, d = _.fieldPathId) : (h = re(h, [Me, y]), h = h && l.retrieveSchema(h)), $ = _g(h == null ? void 0 : h.readOnly, $), h && (Ae(h, Ne) || Ae(h, be))) {
      const E = Ae(h, Ne) ? Ne : be, k = zn(h);
      v = { options: h[E], hasDiscriminator: !!k };
    }
  }
  return { schema: h, isRequired: w, isReadonly: $, optionsInfo: v, fieldPathId: d };
}
function NN(e, t) {
  let i = e;
  return Vr(i) && (i = Id(t, i)), Bs(i) ? i : null;
}
function IN(e, t) {
  let i, o = null, a = {}, l;
  if (Vr(t) || i_(t))
    i = t ?? "";
  else {
    const { name: c = "", render: f, ...d } = t;
    i = c, a = d, dt(a) || eN(a, (m, y) => {
      if (Vr(m)) {
        const h = ON.exec(m);
        if (Array.isArray(h) && h.length > 1) {
          const S = h[1];
          a[y] = Id(e, S, S);
        }
      }
    }), o = NN(f, e), !c && o && (l = D.jsx(o, { ...d, "data-testid": Mr.uiComponent }));
  }
  return { name: i, UIComponent: o, uiProps: a, rendered: l };
}
function eu(e) {
  const { childrenLayoutGridSchemaId: t, ...i } = e, { registry: o, schema: a, formData: l } = i, { schemaUtils: c } = o, f = c.retrieveSchema(a, l);
  return t.map((d) => fe.createElement(xd, { ...i, key: `layoutGrid-${Dn(d)}`, schema: f, layoutGridSchema: d }));
}
function jN(e) {
  const { layoutGridSchema: t, ...i } = e, { formData: o, registry: a } = i, { children: l, gridProps: c } = Zl(t, Mn.CONDITION, a), { operator: f, field: d = "", value: m } = c, y = re(o, d, null);
  return kN(f, y, m) ? D.jsx(eu, { ...i, childrenLayoutGridSchemaId: l }) : null;
}
function AN(e) {
  const { layoutGridSchema: t, ...i } = e, { registry: o, uiSchema: a } = i, { children: l, gridProps: c } = Zl(t, Mn.COLUMN, o), f = Ee(a), d = ke("GridTemplate", o, f);
  return D.jsx(d, { column: !0, "data-testid": Mr.col, ...c, children: D.jsx(eu, { ...i, childrenLayoutGridSchemaId: l }) });
}
function xN(e) {
  const { layoutGridSchema: t, ...i } = e, { registry: o, uiSchema: a } = i, { children: l, gridProps: c } = Zl(t, Mn.COLUMNS, o), f = Ee(a), d = ke("GridTemplate", o, f);
  return l.map((m) => D.jsx(d, { column: !0, "data-testid": Mr.col, ...c, children: D.jsx(eu, { ...i, childrenLayoutGridSchemaId: [m] }) }, `column-${Dn(m)}`));
}
function bN(e) {
  const { layoutGridSchema: t, ...i } = e, { registry: o, uiSchema: a } = i, { children: l, gridProps: c } = Zl(t, Mn.ROW, o), f = Ee(a), d = ke("GridTemplate", o, f);
  return D.jsx(d, { ...c, "data-testid": Mr.row, children: D.jsx(eu, { ...i, childrenLayoutGridSchemaId: l }) });
}
function FN(e) {
  const {
    gridSchema: t,
    schema: i,
    uiSchema: o,
    errorSchema: a,
    fieldPathId: l,
    onBlur: c,
    onFocus: f,
    formData: d,
    readonly: m,
    registry: y,
    layoutGridSchema: h,
    // Used to pull this out of otherProps since we don't want to pass it through
    ...S
  } = e, { onChange: $ } = S, { fields: v } = y, { SchemaField: w, LayoutMultiSchemaField: _ } = v, E = IN(y, t), { name: k, UIComponent: j, uiProps: T } = E, { schema: N, isRequired: x, isReadonly: F, optionsInfo: V, fieldPathId: U } = TN(y, k, i, d, l), G = Ci(U);
  if (E.rendered)
    return E.rendered;
  if (N) {
    const Q = V != null && V.hasDiscriminator ? _ : w, { fieldUiSchema: H, uiReadonly: q } = CN(k, T, o, F, m);
    return D.jsx(Q, { "data-testid": V != null && V.hasDiscriminator ? Mr.layoutMultiSchemaField : Mr.field, ...S, name: k, required: x, readonly: q, schema: N, uiSchema: H, errorSchema: re(a, k), fieldPathId: G, formData: re(d, k), onChange: $, onBlur: c, onFocus: f, options: V == null ? void 0 : V.options, registry: y });
  }
  return j ? D.jsx(j, { "data-testid": Mr.uiComponent, ...S, name: k, required: x, formData: d, readOnly: !!F || m, errorSchema: a, uiSchema: o, schema: i, fieldPathId: l, onBlur: c, onFocus: f, registry: y, ...T }) : null;
}
function xd(e) {
  const { uiSchema: t } = e;
  let { layoutGridSchema: i } = e;
  const o = Ee(t);
  if (!i && hf in o && Fe(o[hf]) && (i = o[hf]), Fe(i)) {
    if (Mn.ROW in i)
      return D.jsx(bN, { ...e, layoutGridSchema: i });
    if (Mn.COLUMN in i)
      return D.jsx(AN, { ...e, layoutGridSchema: i });
    if (Mn.COLUMNS in i)
      return D.jsx(xN, { ...e, layoutGridSchema: i });
    if (Mn.CONDITION in i)
      return D.jsx(jN, { ...e, layoutGridSchema: i });
  }
  return D.jsx(FN, { ...e, gridSchema: i });
}
xd.TEST_IDS = Mr;
function RN(e) {
  const { fieldPathId: t, title: i, schema: o, uiSchema: a, required: l, registry: c, name: f } = e, d = Ee(a, c.globalUiOptions), { title: m } = d, { title: y } = o, h = m || i || y || f;
  if (!h)
    return null;
  const S = ke("TitleFieldTemplate", c, d);
  return D.jsx(S, { id: Nd(t), title: h, required: l, schema: o, uiSchema: a, registry: c });
}
function mf(e, t, i) {
  const o = "!@#!@$@#$!@$#";
  return e.map(({ schema: l }) => l).find((l) => {
    const c = re(l, [Me, t]);
    return re(c, Vl, re(c, on, o)) === i;
  });
}
function wg(e, t, i, o, a) {
  const l = t.map((d) => i.retrieveSchema(d, a));
  let c = e;
  Ae(e, Ne) ? c = { ...e, [Ne]: l } : Ae(e, be) && (c = { ...e, [be]: l });
  const f = yo(c, o);
  if (!f)
    throw new Error(`No enumOptions were computed from the schema ${JSON.stringify(c)}`);
  return f;
}
function DN(e) {
  var nt;
  const { name: t, baseType: i, disabled: o = !1, formData: a, fieldPathId: l, onBlur: c, onChange: f, options: d, onFocus: m, registry: y, uiSchema: h, schema: S, autofocus: $, readonly: v, required: w, errorSchema: _, hideError: E = !1 } = e, { widgets: k, schemaUtils: j, globalUiOptions: T } = y, [N, x] = fe.useState(wg(S, d, j, h, a)), F = re(l, Ke), V = zn(S), U = ke("FieldErrorTemplate", y, d), G = ke("FieldTemplate", y, d), Q = Dn(S), H = Dn(d), q = h ? Dn(h) : "", le = a ? Dn(a) : "";
  fe.useEffect(() => {
    x(wg(S, d, j, h, a));
  }, [Q, H, j, q, le]);
  const { widget: ie = V ? "radio" : "select", title: ne = "", placeholder: pe = "", optionsSchemaSelector: Z = V, hideError: ae, ...z } = Ee(h);
  if (!Z)
    throw new Error("No selector field provided for the LayoutMultiSchemaField");
  const P = re(a, Z);
  let b = re((nt = N[0]) == null ? void 0 : nt.schema, [Me, Z], {});
  const R = mf(N, Z, P);
  b = b != null && b.type ? b : { ...b, type: (R == null ? void 0 : R.type) || i };
  const C = Vn(b, ie, k), I = ae === void 0 ? E : !!ae, B = re(_, [$t], []), X = Fs(_, [$t]), J = j.getDisplayLabel(S, h, T), se = (ot) => {
    const ze = mf(N, Z, ot), Rt = mf(N, Z, P);
    let et = j.sanitizeDataForNewSchema(ze, Rt, a);
    et && ze && (et = j.getDefaultFormState(ze, et, "excludeObjectChildren")), et && Be(et, Z, ot), f(et, l.path, void 0, F);
  }, ce = { enumOptions: N, ...z }, $e = !I && B.length > 0 ? D.jsx(U, { fieldPathId: l, schema: S, errors: B, registry: y }) : void 0;
  return D.jsx(G, { id: F, schema: S, label: (ne || S.title) ?? "", disabled: o || Array.isArray(N) && dt(N), uiSchema: h, required: w, readonly: !!v, registry: y, displayLabel: J, errors: $e, onChange: f, onKeyRename: _l, onKeyRenameBlur: _l, onRemoveProperty: _l, children: D.jsx(C, { id: F, name: t, schema: S, label: (ne || S.title) ?? "", disabled: o || Array.isArray(N) && dt(N), uiSchema: h, autofocus: $, readonly: v, required: w, registry: y, multiple: !1, rawErrors: B, hideError: I, hideLabel: !J, errorSchema: X, placeholder: pe, onChange: se, onBlur: c, onFocus: m, value: P, options: ce, htmlName: l.name }) });
}
class Eg extends fe.Component {
  /** Constructs an `AnyOfField` with the given `props` to initialize the initially selected option in state
   *
   * @param props - The `FieldProps` for this template
   */
  constructor(i) {
    super(i);
    /** Callback handler to remember what the currently selected option is. In addition to that the `formData` is updated
     * to remove properties that are not part of the newly selected option schema, and then the updated data is passed to
     * the `onChange` handler.
     *
     * @param option - The new option value being selected
     */
    bt(this, "onOptionChange", (i) => {
      const { selectedOption: o, retrievedOptions: a } = this.state, { formData: l, onChange: c, registry: f, fieldPathId: d } = this.props, { schemaUtils: m } = f, y = i !== void 0 ? parseInt(i, 10) : -1;
      if (y === o)
        return;
      const h = y >= 0 ? a[y] : void 0, S = o >= 0 ? a[o] : void 0;
      let $ = m.sanitizeDataForNewSchema(h, S, l);
      h && ($ = m.getDefaultFormState(h, $, "excludeObjectChildren")), this.setState({ selectedOption: y }, () => {
        c($, d.path, void 0, this.getFieldId());
      });
    });
    const { formData: o, options: a, registry: { schemaUtils: l } } = this.props, c = a.map((f) => l.retrieveSchema(f, o));
    this.state = {
      retrievedOptions: c,
      selectedOption: this.getMatchingOption(0, o, c)
    };
  }
  /** React lifecycle method that is called when the props and/or state for this component is updated. It recomputes the
   * currently selected option based on the overall `formData`
   *
   * @param prevProps - The previous `FieldProps` for this template
   * @param prevState - The previous `AnyOfFieldState` for this template
   */
  componentDidUpdate(i, o) {
    const { formData: a, options: l, fieldPathId: c } = this.props, { selectedOption: f } = this.state;
    let d = this.state;
    if (!Ge(i.options, l)) {
      const { registry: { schemaUtils: m } } = this.props, y = l.map((h) => m.retrieveSchema(h, a));
      d = { selectedOption: f, retrievedOptions: y };
    }
    if (!Ge(a, i.formData) && c.$id === i.fieldPathId.$id) {
      const { retrievedOptions: m } = d, y = this.getMatchingOption(f, a, m);
      o && y !== f && (d = { selectedOption: y, retrievedOptions: m });
    }
    d !== this.state && this.setState(d);
  }
  /** Determines the best matching option for the given `formData` and `options`.
   *
   * @param formData - The new formData
   * @param options - The list of options to choose from
   * @return - The index of the `option` that best matches the `formData`
   */
  getMatchingOption(i, o, a) {
    const { schema: l, registry: { schemaUtils: c } } = this.props, f = zn(l);
    return c.getClosestMatchingOption(o, a, i, f);
  }
  getFieldId() {
    const { fieldPathId: i, schema: o } = this.props;
    return `${i.$id}${o.oneOf ? "__oneof_select" : "__anyof_select"}`;
  }
  /** Renders the `AnyOfField` selector along with a `SchemaField` for the value of the `formData`
   */
  render() {
    const { name: i, disabled: o = !1, errorSchema: a = {}, formData: l, onBlur: c, onFocus: f, readonly: d, required: m = !1, registry: y, schema: h, uiSchema: S } = this.props, { widgets: $, fields: v, translateString: w, globalUiOptions: _, schemaUtils: E } = y, { SchemaField: k } = v, j = ke("MultiSchemaFieldTemplate", y, _), T = Qs(y, h, m, S), N = $o(l), { selectedOption: x, retrievedOptions: F } = this.state, { widget: V = "select", placeholder: U, autofocus: G, autocomplete: Q, title: H = h.title, ...q } = Ee(S, _), le = Vn({ type: "number" }, V, $), ie = re(a, $t, []), ne = Fs(a, [$t]), pe = E.getDisplayLabel(h, S, _), Z = x >= 0 && F[x] || null;
    let ae;
    if (Z) {
      const { required: X } = h;
      ae = X ? ir({ required: X }, Z) : Z;
    }
    let z = [];
    Ne in h && S && Ne in S ? Array.isArray(S[Ne]) ? z = S[Ne] : console.warn(`uiSchema.oneOf is not an array for "${H || i}"`) : be in h && S && be in S && (Array.isArray(S[be]) ? z = S[be] : console.warn(`uiSchema.anyOf is not an array for "${H || i}"`));
    let P = S;
    x >= 0 && z.length > x && (P = z[x]);
    const b = H ? Le.TitleOptionPrefix : Le.OptionPrefix, R = H ? [H] : [], C = F.map((X, J) => {
      const { title: se = X.title } = Ee(z[J]);
      return {
        label: se || w(b, R.concat(String(J + 1))),
        value: J
      };
    }), I = !T || N ? D.jsx(le, { id: this.getFieldId(), name: `${i}${h.oneOf ? "__oneof_select" : "__anyof_select"}`, schema: { type: "number", default: 0 }, onChange: this.onOptionChange, onBlur: c, onFocus: f, disabled: o || dt(C), multiple: !1, rawErrors: ie, errorSchema: ne, value: x >= 0 ? x : void 0, options: { enumOptions: C, ...q }, registry: y, placeholder: U, autocomplete: Q, autofocus: G, label: H ?? i, hideLabel: !pe, readonly: d }) : void 0, B = ae && ae.type !== "null" && D.jsx(k, { ...this.props, schema: ae, uiSchema: P }) || null;
    return D.jsx(j, { schema: h, registry: y, uiSchema: S, selector: I, optionSchemaField: B });
  }
}
const MN = /\.([0-9]*0)*$/, LN = /[0.]0*$/;
function UN(e) {
  const { registry: t, onChange: i, formData: o, value: a } = e, [l, c] = fe.useState(a), { StringField: f } = t.fields;
  let d = o;
  const m = fe.useCallback((y, h, S, $) => {
    c(y), `${y}`.charAt(0) === "." && (y = `0${y}`);
    const v = typeof y == "string" && y.match(MN) ? gy(y.replace(LN, "")) : gy(y);
    i(v, h, S, $);
  }, [i]);
  if (typeof l == "string" && typeof d == "number") {
    const y = new RegExp(`^(${String(d).replace(".", "\\.")})?\\.?0*$`);
    l.match(y) && (d = l);
  }
  return D.jsx(f, { ...e, formData: d, onChange: m });
}
function xn() {
  return xn = Object.assign ? Object.assign.bind() : function(e) {
    for (var t = 1; t < arguments.length; t++) {
      var i = arguments[t];
      for (var o in i) ({}).hasOwnProperty.call(i, o) && (e[o] = i[o]);
    }
    return e;
  }, xn.apply(null, arguments);
}
const ul = ["strong", "em", "del", "mark"], $g = [["**", ul[0]], ["__", ul[0]], ["~~", ul[2]], ["==", ul[3]], ["*", "em"], ["_", "em"]];
function zN(e, t) {
  for (var i = 1, o = t + 1; o < e.length && i > 0; ) e[o] !== "\\" ? (e[o] === "[" && i++, e[o] === "]" && i--, o++) : o += 2;
  if (i === 0 && o < e.length && (e[o] === "(" || e[o] === "[")) {
    var a = e[o] === "(" ? ")" : "]", l = 1;
    for (o++; o < e.length && l > 0; ) e[o] !== "\\" ? (e[o] === "(" && a === ")" && l++, e[o] === a && l--, o++) : o += 2;
    if (l === 0) return o;
  }
  return -1;
}
function VN(e, t) {
  if (!t || !t.inline && !t.simple) return null;
  var i = e[0];
  if (i !== "*" && i !== "_" && i !== "~" && i !== "=") return null;
  for (var o = "", a = 0, l = "", c = 0; c < 6; c++) {
    var f = $g[c][0];
    if (e.startsWith(f) && e.length >= 2 * f.length) {
      o = f, a = f.length, l = $g[c][1];
      break;
    }
  }
  if (!o) return null;
  for (var d = a, m = !1, y = !1, h = "", S = 0, $ = "", v = !1, w = ""; d < e.length; ) {
    var _ = e[d];
    if (v) $ += _, v = !1, w = _, d++;
    else if (_ !== "\\") if (_ !== "`" || S !== 0) {
      if (_ === "[" && !m && S === 0) {
        var E = zN(e, d);
        if (E !== -1) {
          $ += e.slice(d, E), d = E, w = e[E - 1];
          continue;
        }
      }
      if (y) $ += _, h ? _ === h && (h = "") : _ === '"' || _ === "'" ? h = _ : _ === ">" && (y = !1), w = _, d++;
      else if (_ !== "<" || m) {
        if (_ === `
` && w === `
` && !m && S === 0) return null;
        if (!m && S === 0) {
          for (var k = 0; d + k < e.length && e[d + k] === o[0]; ) k++;
          if (k >= a && (a !== 1 || o !== "*" && o !== "_" || e[d - 1] !== o && e[d + 1] !== o)) {
            var j = [e.slice(0, d + k), l, $ + e.slice(d + a, d + k)];
            return j.index = 0, j.input = e, j;
          }
        }
        $ += _, w = _, d++;
      } else {
        var T = e[d + 1], N = e.indexOf(">", d);
        if (N !== -1) {
          var x = e.slice(d, N + 1).endsWith("/>");
          T === "/" ? S = Math.max(0, S - 1) : x || S++;
        }
        y = !0, $ += _, w = _, d++;
      }
    } else m = !m, $ += _, w = _, d++;
    else $ += _, v = !0, w = _, d++;
  }
  return null;
}
const BN = ["children", "options"], Og = ["allowFullScreen", "allowTransparency", "autoComplete", "autoFocus", "autoPlay", "cellPadding", "cellSpacing", "charSet", "classId", "colSpan", "contentEditable", "contextMenu", "crossOrigin", "encType", "formAction", "formEncType", "formMethod", "formNoValidate", "formTarget", "frameBorder", "hrefLang", "inputMode", "keyParams", "keyType", "marginHeight", "marginWidth", "maxLength", "mediaGroup", "minLength", "noValidate", "radioGroup", "readOnly", "rowSpan", "spellCheck", "srcDoc", "srcLang", "srcSet", "tabIndex", "useMap"].reduce((e, t) => (e[t.toLowerCase()] = t, e), { class: "className", for: "htmlFor" }), Pg = { amp: "&", apos: "'", gt: ">", lt: "<", nbsp: " ", quot: "“" }, KN = ["style", "script", "pre"], WN = ["src", "href", "data", "formAction", "srcDoc", "action"], HN = /([-A-Z0-9_:]+)(?:\s*=\s*(?:(?:"((?:\\.|[^"])*)")|(?:'((?:\\.|[^'])*)')|(?:\{((?:\\.|{[^}]*?}|[^}])*)\})))?/gi, qN = /\n{2,}$/, Cg = /^(\s*>[\s\S]*?)(?=\n\n|$)/, GN = /^ *> ?/gm, YN = /^(?:\[!([^\]]*)\]\n)?([\s\S]*)/, QN = /^ {2,}\n/, JN = /^(?:([-*_])( *\1){2,}) *(?:\n *)+\n/, kg = /^(?: {1,3})?(`{3,}|~{3,}) *(\S+)? *([^\n]*?)?\n([\s\S]*?)(?:\1\n?|$)/, Tg = /^(?: {4}[^\n]+\n*)+(?:\n *)+\n?/, XN = /^(`+)((?:\\`|(?!\1)`|[^`])+)\1/, ZN = /^(?:\n *)*\n/, eI = /\r\n?/g, tI = /^\[\^([^\]]+)](:(.*)((\n+ {4,}.*)|(\n(?!\[\^).+))*)/, nI = /^\[\^([^\]]+)]/, rI = /\f/g, iI = /^---[ \t]*\n(.|\n)*\n---[ \t]*\n/, oI = /^\[(x|\s)\]/, Ng = /^(#{1,6}) *([^\n]+?)(?: +#*)?(?:\n *)*(?:\n|$)/, Ig = /^ *(#{1,6}) +([^\n]+?)(?: +#*)?(?:\n *)*(?:\n|$)/, jg = /^([^\n]+)\n *(=|-)\2{2,} *\n/, bd = /^<([a-z][^ >/]*) ?((?:[^>]*[^/])?)>/i;
function sI(e) {
  const t = bd.exec(e);
  if (!t) return null;
  const i = t[1], o = i.toLowerCase(), a = o.length + 1;
  let l = t[0].length;
  e[l] === `
` && l++;
  const c = l;
  let f = l, d = 1;
  const m = e.length;
  for (; d > 0; ) {
    const h = e.indexOf("<", l);
    if (h === -1) return null;
    let S = -1, $ = -1;
    if (e[h + 1] === "/") $ = h;
    else if (e[h + 1] === o[0] || e[h + 1] === i[0]) {
      let v = !0;
      for (let w = 0; w < o.length; w++) {
        const _ = e[h + 1 + w];
        if (_ !== o[w] && _ !== i[w]) {
          v = !1;
          break;
        }
      }
      !v || e[h + a] !== " " && e[h + a] !== ">" || (S = h);
    }
    if (S !== -1 || $ !== -1) if (S !== -1 && ($ === -1 || S < $)) l = S + a + 1, d++;
    else {
      let v = $ + 2;
      for (; v < m; ) {
        const _ = e[v];
        if (_ !== " " && _ !== "	" && _ !== `
` && _ !== "\r") break;
        v++;
      }
      if (v + o.length > m) return null;
      let w = !0;
      for (let _ = 0; _ < o.length; _++) {
        const E = e[v + _];
        if (E !== o[_] && E !== i[_]) {
          w = !1;
          break;
        }
      }
      if (!w) {
        l = v;
        continue;
      }
      for (v += o.length; v < m; ) {
        const _ = e[v];
        if (_ !== " " && _ !== "	" && _ !== `
` && _ !== "\r") break;
        v++;
      }
      if (v >= m || e[v] !== ">") {
        l = v;
        continue;
      }
      f = $, l = v + 1, d--;
    }
    else l = h + 1;
  }
  let y = 0;
  for (; l + y < m && e[l + y] === `
`; ) y++;
  return [e.slice(0, l + y), i, t[2], e.slice(c, f)];
}
const aI = /&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-fA-F]{1,6});/gi, Ag = /^<!--[\s\S]*?(?:-->)/, lI = /^(data|aria|x)-[a-z_][a-z\d_.-]*$/, Uf = /^ *<([a-z][a-z0-9:]*)(?:\s+((?:<.*?>|[^>])*))?\/?>(?!<\/\1>)(\s*\n)?/i, uI = /^\{.*\}$/, cI = /^(https?:\/\/[^\s<]+[^<.,:;"')\]\s])/, fI = /^<([^ >]+[:@\/][^ >]+)>/, dI = /-([a-z])?/gi, xg = /^(\|.*)\n(?: *(\|? *[-:]+ *\|[-| :]*)\n((?:.*\|.*\n)*))?\n?/, pI = /^[^\n]+(?:  \n|\n{2,})/, hI = /^\[([^\]]*)\]:\s+<?([^\s>]+)>?\s*("([^"]*)")?/, mI = /^!\[([^\]]*)\] ?\[([^\]]*)\]/, yI = /^\[([^\]]*)\] ?\[([^\]]*)\]/, gI = /(\n|^[-*]\s|^#|^ {2,}|^-{2,}|^>\s)/, vI = /\t/g, _I = /(^ *\||\| *$)/g, SI = /^ *:-+: *$/, wI = /^ *:-+ *$/, EI = /^ *-+: *$/, $I = /^(:[a-zA-Z0-9-_]+:)/, OI = /^\\([^0-9A-Za-z\s])/, PI = /\\([^0-9A-Za-z\s])/g, CI = /^[\s\S](?:(?!  \n|[0-9]\.|http)[^=*_~\-\n:<`\\\[!])*/, kI = /^\n+/, TI = /^([ \t]*)/, NI = /(?:^|\n)( *)$/, Fd = "(?:\\d+\\.)", Rd = "(?:[*+-])";
function o_(e) {
  return "( *)(" + (e === 1 ? Fd : Rd) + ") +";
}
const s_ = o_(1), a_ = o_(2);
function l_(e) {
  return RegExp("^" + (e === 1 ? s_ : a_));
}
const II = l_(1), jI = l_(2);
function u_(e) {
  return RegExp("^" + (e === 1 ? s_ : a_) + "[^\\n]*(?:\\n(?!\\1" + (e === 1 ? Fd : Rd) + " )[^\\n]*)*(\\n|$)", "gm");
}
const AI = u_(1), xI = u_(2);
function c_(e) {
  const t = e === 1 ? Fd : Rd;
  return RegExp("^( *)(" + t + ") [\\s\\S]+?(?:\\n{2,}(?! )(?!\\1" + t + " (?!" + t + " ))\\n*|\\s*\\n*$)");
}
const f_ = c_(1), d_ = c_(2);
function bg(e, t) {
  const i = t === 1, o = i ? f_ : d_, a = i ? AI : xI, l = i ? II : jI;
  return { t: (c) => l.test(c), o: xr(function(c, f) {
    const d = NI.exec(f.prevCapture);
    return d && (f.list || !f.inline && !f.simple) ? o.exec(c = d[1] + c) : null;
  }), u: 1, i(c, f, d) {
    const m = i ? +c[2] : void 0, y = c[0].replace(qN, `
`).match(a), h = l.exec(y[0]), S = RegExp("^ {1," + (h ? h[0].length : 0) + "}", "gm");
    let $ = !1;
    return { items: y.map(function(v, w) {
      const _ = v.replace(S, "").replace(l, ""), E = w === y.length - 1, k = In(_, `

`) || E && $;
      $ = k;
      const j = d.inline, T = d.list;
      let N;
      d.list = !0, k ? (d.inline = !1, N = Os(_) + `

`) : (d.inline = !0, N = Os(_));
      const x = f(N, d);
      return d.inline = j, d.list = T, x;
    }), ordered: i, start: m };
  } };
}
const bI = RegExp(`^\\[((?:\\[[^\\[\\]]*(?:\\[[^\\[\\]]*\\][^\\[\\]]*)*\\]|[^\\[\\]])*)\\]\\(\\s*<?((?:\\([^)]*\\)|[^\\s\\\\]|\\\\.)*?)>?(?:\\s+['"]([\\s\\S]*?)['"])?\\s*\\)`), FI = /^!\[(.*?)\]\( *((?:\([^)]*\)|[^() ])*) *"?([^)"]*)?"?\)/;
function Fg(e) {
  return typeof e == "string";
}
function Os(e) {
  let t = e.length;
  for (; t > 0 && e[t - 1] <= " "; ) t--;
  return e.slice(0, t);
}
function zf(e, t) {
  return e.startsWith(t);
}
function In(e, t) {
  return e.indexOf(t) !== -1;
}
function RI(e, t, i) {
  if (Array.isArray(i)) {
    for (let o = 0; o < i.length; o++) if (zf(e, i[o])) return !0;
    return !1;
  }
  return i(e, t);
}
function ps(e) {
  return e.replace(/[ÀÁÂÃÄÅàáâãäåæÆ]/g, "a").replace(/[çÇ]/g, "c").replace(/[ðÐ]/g, "d").replace(/[ÈÉÊËéèêë]/g, "e").replace(/[ÏïÎîÍíÌì]/g, "i").replace(/[Ññ]/g, "n").replace(/[øØœŒÕõÔôÓóÒò]/g, "o").replace(/[ÜüÛûÚúÙù]/g, "u").replace(/[ŸÿÝý]/g, "y").replace(/[^a-z0-9- ]/gi, "").replace(/ /gi, "-").toLowerCase();
}
function DI(e) {
  return EI.test(e) ? "right" : SI.test(e) ? "center" : wI.test(e) ? "left" : null;
}
function Rg(e, t, i, o) {
  const a = i.inTable;
  i.inTable = !0;
  let l = [[]], c = "";
  function f() {
    if (!c) return;
    const d = l[l.length - 1];
    d.push.apply(d, t(c, i)), c = "";
  }
  return e.trim().split(/(`[^`]*`|\\\||\|)/).filter(Boolean).forEach((d, m, y) => {
    d.trim() === "|" && (f(), o) ? m !== 0 && m !== y.length - 1 && l.push([]) : c += d;
  }), f(), i.inTable = a, l;
}
function MI(e, t, i) {
  i.inline = !0;
  const o = e[2] ? e[2].replace(_I, "").split("|").map(DI) : [], a = e[3] ? function(c, f, d) {
    return c.trim().split(`
`).map(function(m) {
      return Rg(m, f, d, !0);
    });
  }(e[3], t, i) : [], l = Rg(e[1], t, i, !!a.length);
  return i.inline = !1, a.length ? { align: o, cells: a, header: l, type: "25" } : { children: l, type: "21" };
}
function Dg(e, t) {
  return e.align[t] == null ? {} : { textAlign: e.align[t] };
}
function xr(e) {
  return e.inline = 1, e;
}
function Tr(e) {
  return xr(function(t, i) {
    return i.inline ? e.exec(t) : null;
  });
}
function cl(e) {
  return xr(function(t, i) {
    return i.inline || i.simple ? e.exec(t) : null;
  });
}
function er(e) {
  return function(t, i) {
    return i.inline || i.simple ? null : e.exec(t);
  };
}
function Mg(e) {
  return xr(function(t) {
    return e.exec(t);
  });
}
const LI = /(javascript|vbscript|data(?!:image)):/i;
function UI(e) {
  try {
    const t = decodeURIComponent(e).replace(/[^A-Za-z0-9/:]/g, "");
    if (LI.test(t)) return null;
  } catch {
    return null;
  }
  return e;
}
function jn(e) {
  return e && e.replace(PI, "$1");
}
function Pl(e, t, i) {
  const o = i.inline || !1, a = i.simple || !1;
  i.inline = !0, i.simple = !0;
  const l = e(t, i);
  return i.inline = o, i.simple = a, l;
}
function zI(e, t, i) {
  const o = i.inline || !1, a = i.simple || !1;
  i.inline = !1, i.simple = !0;
  const l = e(t, i);
  return i.inline = o, i.simple = a, l;
}
function VI(e, t, i) {
  const o = i.inline || !1;
  i.inline = !1;
  const a = e(t, i);
  return i.inline = o, a;
}
const BI = (e, t, i) => ({ children: Pl(t, e[2], i) });
function yf() {
  return {};
}
function KI(...e) {
  return e.filter(Boolean).join(" ");
}
function gf(e, t, i) {
  let o = e;
  const a = t.split(".");
  for (; a.length && (o = o[a[0]], o !== void 0); ) a.shift();
  return o || i;
}
function vf(e, t, i, o) {
  if (!t || !t.trim()) return null;
  const a = t.match(HN);
  return a ? a.reduce(function(l, c) {
    const f = c.indexOf("=");
    if (f !== -1) {
      const d = function(h) {
        return h.indexOf("-") !== -1 && h.match(lI) === null && (h = h.replace(dI, function(S, $) {
          return $.toUpperCase();
        })), h;
      }(c.slice(0, f)).trim(), m = Og[d] || d;
      if (m === "ref") return l;
      const y = l[m] = function(h, S, $, v) {
        return S === "style" ? function(w) {
          const _ = [];
          if (!w) return _;
          let E = "", k = 0, j = "";
          for (let N = 0; N < w.length; N++) {
            const x = w[N];
            if (x === '"' || x === "'") j ? x === j && (j = "", k--) : (j = x, k++);
            else if (x === "(" && E.endsWith("url")) k++;
            else if (x === ")" && k > 0) k--;
            else if (x === ";" && k === 0) {
              const F = E.indexOf(":");
              F > 0 && _.push([E.slice(0, F).trim(), E.slice(F + 1).trim()]), E = "";
              continue;
            }
            E += x;
          }
          const T = E.indexOf(":");
          return T > 0 && _.push([E.slice(0, T).trim(), E.slice(T + 1).trim()]), _;
        }($).reduce(function(w, [_, E]) {
          return w[_.replace(/(-[a-z])/g, (k) => k[1].toUpperCase())] = v(E, h, _), w;
        }, {}) : WN.indexOf(S) !== -1 ? v(jn($), h, S) : ($.match(uI) && ($ = jn($.slice(1, $.length - 1))), $ === "true" || $ !== "false" && $);
      }(e, d, function(h) {
        const S = h[0];
        return (S === '"' || S === "'") && h.length >= 2 && h[h.length - 1] === S ? h.slice(1, -1) : h;
      }(c.slice(f + 1).trim()), i);
      typeof y == "string" && (bd.test(y) || Uf.test(y)) && (l[m] = o(y.trim()));
    } else c !== "style" && (l[Og[c] || c] = !0);
    return l;
  }, {}) : null;
}
function Lg(e, t) {
  for (let i = 0; i < e.length; i++) if (e[i].test(t)) return !0;
  return !1;
}
function WI(e = "", t = {}) {
  t.overrides = t.overrides || {}, t.namedCodesToUnicode = t.namedCodesToUnicode ? xn({}, Pg, t.namedCodesToUnicode) : Pg;
  const i = t.slugify || ps, o = t.sanitizer || UI, a = t.createElement || fe.createElement, l = [Cg, kg, Tg, t.enforceAtxHeadings ? Ig : Ng, jg, xg, f_, d_], c = [...l, pI, bd, Ag, Uf];
  function f(v, w, ..._) {
    const E = gf(t.overrides, v + ".props", {});
    return a(function(k, j) {
      const T = gf(j, k);
      return T ? typeof T == "function" || typeof T == "object" && "render" in T ? T : gf(j, k + ".component", k) : k;
    }(v, t.overrides), xn({}, w, E, { className: KI(w == null ? void 0 : w.className, E.className) || void 0 }), ..._);
  }
  function d(v) {
    v = v.replace(iI, "");
    let w = !1;
    t.forceInline ? w = !0 : t.forceBlock || (w = gI.test(v) === !1);
    const _ = S(w ? v : Os(v).replace(kI, "") + `

`, { inline: w });
    if (t.ast) return _;
    const E = $(_);
    for (; Fg(E[E.length - 1]) && !E[E.length - 1].trim(); ) E.pop();
    if (m.length && E.push(f("footer", { key: "footer" }, m.map(function(T) {
      return f("div", { id: i(T.identifier, ps), key: T.identifier }, T.identifier, $(S(T.footnote, { inline: !0 })));
    }))), t.wrapper === null) return E;
    const k = t.wrapper || (w ? "span" : "div");
    let j;
    if (E.length > 1 || t.forceWrapper) j = E;
    else {
      if (E.length === 1) return j = E[0], typeof j == "string" ? f("span", { key: "outer" }, j) : j;
      j = null;
    }
    return a(k, xn({ key: "outer" }, t.wrapperProps), j);
  }
  const m = [], y = {}, h = { 0: { t: [">"], o: er(Cg), u: 1, i(v, w, _) {
    const [, E, k] = v[0].replace(GN, "").match(YN);
    return { alert: E, children: w(k, _) };
  } }, 1: { t: ["  "], o: Tr(QN), u: 1, i: yf }, 2: { t: function(v, w) {
    if (w.inline || w.simple) return !1;
    var _ = v[0];
    return _ === "-" || _ === "*" || _ === "_";
  }, o: er(JN), u: 1, i: yf }, 3: { t: ["    "], o: er(Tg), u: 0, i: (v) => ({ lang: void 0, text: jn(Os(v[0].replace(/^ {4}/gm, ""))) }) }, 4: { t: ["```", "~~~"], o: er(kg), u: 0, i: (v) => ({ attrs: vf("code", v[3] || "", o, d), lang: v[2] || void 0, text: v[4], type: "3" }) }, 5: { t: ["`"], o: cl(XN), u: 3, i: (v) => ({ text: jn(v[2]) }) }, 6: { t: ["[^"], o: er(tI), u: 0, i: (v) => (m.push({ footnote: v[2], identifier: v[1] }), {}) }, 7: { t: ["[^"], o: Tr(nI), u: 1, i: (v) => ({ target: "#" + i(v[1], ps), text: v[1] }) }, 8: { t: ["[ ]", "[x]"], o: Tr(oI), u: 1, i: (v) => ({ completed: v[1].toLowerCase() === "x" }) }, 9: { t: ["#"], o: er(t.enforceAtxHeadings ? Ig : Ng), u: 1, i: (v, w, _) => ({ children: Pl(w, v[2], _), id: i(v[2], ps), level: v[1].length }) }, 10: { t: (v) => {
    const w = v.indexOf(`
`);
    return w > 0 && w < v.length - 1 && (v[w + 1] === "=" || v[w + 1] === "-");
  }, o: er(jg), u: 1, i: (v, w, _) => ({ children: Pl(w, v[1], _), level: v[2] === "=" ? 1 : 2, type: "9" }) }, 11: { t: ["<"], o: xr(sI), u: 1, i(v, w, _) {
    const [, E] = v[3].match(TI), k = RegExp("^" + E, "gm"), j = v[3].replace(k, ""), T = Lg(c, j) ? VI : Pl, N = v[1].toLowerCase(), x = KN.indexOf(N) !== -1, F = (x ? N : v[1]).trim(), V = { attrs: vf(F, v[2], o, d), noInnerParse: x, tag: F };
    if (_.inAnchor = _.inAnchor || N === "a", x) V.text = v[3];
    else {
      const U = _.inHTML;
      _.inHTML = !0, V.children = T(w, j, _), _.inHTML = U;
    }
    return _.inAnchor = !1, V;
  } }, 13: { t: ["<"], o: Mg(Uf), u: 1, i(v) {
    const w = v[1].trim();
    return { attrs: vf(w, v[2] || "", o, d), tag: w };
  } }, 12: { t: ["<!--"], o: Mg(Ag), u: 1, i: () => ({}) }, 14: { t: ["!["], o: cl(FI), u: 1, i: (v) => ({ alt: jn(v[1]), target: jn(v[2]), title: jn(v[3]) }) }, 15: { t: ["["], o: Tr(bI), u: 3, i: (v, w, _) => ({ children: zI(w, v[1], _), target: jn(v[2]), title: jn(v[3]) }) }, 16: { t: function(v, w) {
    return !(!w.inline || w.inAnchor) && v[0] === "<" && (In(v, ":") || In(v, "@") || In(v, "/"));
  }, o: Tr(fI), u: 0, i(v) {
    let w = v[1], _ = !1;
    return In(w, "@") && !In(w, "//") && (_ = !0, w = w.replace("mailto:", "")), { children: [{ text: w, type: "27" }], target: _ ? "mailto:" + w : w, type: "15" };
  } }, 17: { t: (v, w) => !w.inAnchor && !t.disableAutoLink && zf(v, "http"), o: Tr(cI), u: 0, i: (v) => ({ children: [{ text: v[1], type: "27" }], target: v[1], title: void 0, type: "15" }) }, 20: bg(0, 1), 30: bg(0, 2), 19: { t: [`
`], o: er(ZN), u: 3, i: yf }, 21: { t: function(v, w) {
    return !w.inline && !w.simple;
  }, o: xr(function(v, w) {
    if (w.inline || w.simple || w.inHTML && !In(v, `

`) && !In(w.prevCapture, `

`)) return null;
    let _ = "", E = 0;
    for (; ; ) {
      const j = v.indexOf(`
`, E), T = v.slice(E, j === -1 ? void 0 : j + 1), N = v[E];
      if ((N === ">" || N === "#" || N === "|" || N === "`" || N === "~" || N === "*" || N === "-" || N === "_" || N === " ") && Lg(l, T) || (_ += T, j === -1 || !T.trim())) break;
      E = j + 1;
    }
    const k = Os(_);
    return k === "" ? null : [_, , k];
  }), u: 3, i: BI }, 22: { t: ["["], o: Tr(hI), u: 0, i: (v) => (y[v[1]] = { target: v[2], title: v[4] }, {}) }, 23: { t: ["!["], o: cl(mI), u: 0, i: (v) => ({ alt: v[1] ? jn(v[1]) : void 0, ref: v[2] }) }, 24: { t: (v) => v[0] === "[" && !In(v, "]("), o: Tr(yI), u: 0, i: (v, w, _) => ({ children: w(v[1], _), fallbackChildren: v[0], ref: v[2] }) }, 25: { t: ["|"], o: er(xg), u: 1, i: MI }, 27: { o: xr(function(v, w) {
    let _;
    return zf(v, ":") && (_ = $I.exec(v)), _ || CI.exec(v);
  }), u: 4, i(v) {
    const w = v[0];
    return { text: In(w, "&") ? w.replace(aI, (_, E) => t.namedCodesToUnicode[E] || _) : w };
  } }, 34: { t: ["*", "_", "~", "="], o: xr(VN), u: 2, i: (v, w, _) => ({ children: w(v[2], _), tag: v[1] }) }, 28: { t: ["\\"], o: cl(OI), u: 1, i: (v) => ({ text: v[1], type: "27" }) } };
  t.disableParsingRawHTML === !0 && (delete h[11], delete h[13]);
  const S = function(v) {
    var w = Object.keys(v);
    function _(E, k) {
      var j = [];
      if (k.prevCapture = k.prevCapture || "", E.trim()) for (; E; ) for (var T = 0; T < w.length; ) {
        var N = w[T], x = v[N];
        if (!x.t || RI(E, k, x.t)) {
          var F = x.o(E, k);
          if (F && F[0]) {
            E = E.substring(F[0].length);
            var V = x.i(F, _, k);
            k.prevCapture += F[0], V.type || (V.type = N), j.push(V);
            break;
          }
          T++;
        } else T++;
      }
      return k.prevCapture = "", j;
    }
    return w.sort(function(E, k) {
      return v[E].u - v[k].u || (E < k ? -1 : 1);
    }), function(E, k) {
      return _(function(j) {
        return j.replace(eI, `
`).replace(rI, "").replace(vI, "    ");
      }(E), k);
    };
  }(h), $ = /* @__PURE__ */ function(v, w, _, E, k) {
    function j(T) {
      return Array.isArray(T) ? T.map((N) => "text" in N ? N.text : "") : "text" in T ? T.text : "";
    }
    return function T(N, x = {}) {
      const F = (x.renderDepth || 0) + 1;
      if (F > 2500) return j(N);
      x.renderDepth = F;
      try {
        if (Array.isArray(N)) {
          const U = x.key, G = [];
          let Q = !1;
          for (let H = 0; H < N.length; H++) {
            x.key = H;
            const q = T(N[H], x), le = Fg(q);
            le && Q ? G[G.length - 1] += q : q !== null && G.push(q), Q = le;
          }
          return x.key = U, x.renderDepth = F - 1, G;
        }
        const V = function(U, G, Q) {
          const H = () => function(q, le, ie, ne, pe, Z, ae) {
            switch (q.type) {
              case "0": {
                const z = { key: ie.key };
                return q.alert && (z.className = "markdown-alert-" + Z(q.alert.toLowerCase(), ps), q.children.unshift({ attrs: {}, children: [{ type: "27", text: q.alert }], noInnerParse: !0, type: "11", tag: "header" })), ne("blockquote", z, le(q.children, ie));
              }
              case "1":
                return ne("br", { key: ie.key });
              case "2":
                return ne("hr", { key: ie.key });
              case "3":
                return ne("pre", { key: ie.key }, ne("code", xn({}, q.attrs, { className: q.lang ? "lang-" + q.lang : "" }), q.text));
              case "5":
                return ne("code", { key: ie.key }, q.text);
              case "7":
                return ne("a", { key: ie.key, href: pe(q.target, "a", "href") }, ne("sup", { key: ie.key }, q.text));
              case "8":
                return ne("input", { checked: q.completed, key: ie.key, readOnly: !0, type: "checkbox" });
              case "9":
                return ne("h" + q.level, { id: q.id, key: ie.key }, le(q.children, ie));
              case "11":
                return ne(q.tag, xn({ key: ie.key }, q.attrs), q.text || (q.children ? le(q.children, ie) : ""));
              case "13":
                return ne(q.tag, xn({}, q.attrs, { key: ie.key }));
              case "14":
                return ne("img", { key: ie.key, alt: q.alt || void 0, title: q.title || void 0, src: pe(q.target, "img", "src") });
              case "15":
                return ne("a", { key: ie.key, href: pe(q.target, "a", "href"), title: q.title }, le(q.children, ie));
              case "23":
                return ae[q.ref] ? ne("img", { key: ie.key, alt: q.alt, src: pe(ae[q.ref].target, "img", "src"), title: ae[q.ref].title }) : null;
              case "24":
                return ae[q.ref] ? ne("a", { key: ie.key, href: pe(ae[q.ref].target, "a", "href"), title: ae[q.ref].title }, le(q.children, ie)) : ne("span", { key: ie.key }, q.fallbackChildren);
              case "25": {
                const z = q;
                return ne("table", { key: ie.key }, ne("thead", null, ne("tr", null, z.header.map(function(P, b) {
                  return ne("th", { key: b, style: Dg(z, b) }, le(P, ie));
                }))), ne("tbody", null, z.cells.map(function(P, b) {
                  return ne("tr", { key: b }, P.map(function(R, C) {
                    return ne("td", { key: C, style: Dg(z, C) }, le(R, ie));
                  }));
                })));
              }
              case "27":
                return q.text;
              case "34":
                return ne(q.tag, { key: ie.key }, le(q.children, ie));
              case "20":
              case "30":
                return ne(q.ordered ? "ol" : "ul", { key: ie.key, start: q.type === "20" ? q.start : void 0 }, q.items.map(function(z, P) {
                  return ne("li", { key: P }, le(z, ie));
                }));
              case "19":
                return `
`;
              case "21":
                return ne("p", { key: ie.key }, le(q.children, ie));
              default:
                return null;
            }
          }(U, G, Q, w, _, E, k);
          return v ? v(H, U, G, Q) : H();
        }(N, T, x);
        return x.renderDepth = F - 1, V;
      } catch (V) {
        if (V instanceof RangeError && V.message.includes("Maximum call stack")) return j(N);
        throw V;
      }
    };
  }(t.renderRule, f, o, i, y);
  return d(e);
}
const Js = (e) => {
  let { children: t, options: i } = e, o = function(a, l) {
    if (a == null) return {};
    var c = {};
    for (var f in a) if ({}.hasOwnProperty.call(a, f)) {
      if (l.indexOf(f) !== -1) continue;
      c[f] = a[f];
    }
    return c;
  }(e, BN);
  return WI(t ?? "", xn({}, i, { wrapperProps: xn({}, i == null ? void 0 : i.wrapperProps, o) }));
}, p_ = Symbol("remove-this-key"), Ug = Symbol("reset");
function HI(e, t) {
  return Array.isArray(e.required) && e.required.indexOf(t) !== -1;
}
function qI(e, t) {
  switch (t) {
    case "array":
      return [];
    case "boolean":
      return !1;
    case "null":
      return null;
    case "number":
      return 0;
    case "object":
      return {};
    case "string":
    default:
      return e(Le.NewStringDefault);
  }
}
function GI(e) {
  const { fieldPathId: t, schema: i, registry: o, uiSchema: a, errorSchema: l, formData: c, onChange: f, onBlur: d, onFocus: m, disabled: y, readonly: h, required: S, hideError: $, propertyName: v, handleKeyRename: w, handleRemoveProperty: _, addedByAdditionalProperties: E } = e, [k, j] = fe.useState(!1), { globalFormOptions: T, fields: N } = o, { SchemaField: x } = N, F = Ci(ln(v, T, t.path)), V = fe.useCallback((H, q, le, ie) => {
    H === void 0 && E && (H = ""), f(H, q, le, ie);
  }, [f, E]), U = fe.useCallback((H) => {
    v !== H && j(!0), w(v, H);
  }, [v, w]), G = fe.useCallback((H) => {
    const { target: { value: q } } = H;
    U(q);
  }, [U]), Q = fe.useCallback(() => {
    _(v);
  }, [v, _]);
  return D.jsx(x, { name: v, required: S, schema: i, uiSchema: a, errorSchema: l, fieldPathId: F, formData: c, wasPropertyKeyModified: k, onKeyRename: U, onKeyRenameBlur: G, onRemoveProperty: Q, onChange: V, onBlur: d, onFocus: m, registry: o, disabled: y, readonly: h, hideError: $ });
}
function YI(e) {
  const { schema: t, uiSchema: i = {}, formData: o, errorSchema: a, fieldPathId: l, name: c, required: f = !1, disabled: d, readonly: m, hideError: y, onBlur: h, onFocus: S, onChange: $, registry: v, title: w } = e, { fields: _, schemaUtils: E, translateString: k, globalUiOptions: j } = v, { OptionalDataControlsField: T } = _, N = E.retrieveSchema(t, o, !0), x = Ee(i, j), { properties: F = {} } = N, V = e.childFieldPathId ?? l, U = x.title ?? N.title ?? w ?? c, G = x.description ?? N.description, Q = Qs(v, N, f, i), H = $o(o);
  let q = [];
  const le = fe.useCallback((P, b) => {
    const { duplicateKeySuffixSeparator: R = "-" } = Ee(i, j);
    let C = 0, I = P;
    for (; Ae(b, I); )
      I = `${P}${R}${++C}`;
    return I;
  }, [i, j]), ie = fe.useCallback(() => {
    if (!(N.additionalProperties || N.patternProperties))
      return;
    const { translateString: P } = v, b = { ...o }, R = le("newKey", b);
    if (N.patternProperties)
      Be(b, R, null);
    else {
      let C, I, B;
      if (Fe(N.additionalProperties)) {
        C = N.additionalProperties.type, I = N.additionalProperties.const, B = N.additionalProperties.default;
        let J = N.additionalProperties;
        if (Ze in J) {
          const { schemaUtils: se } = v;
          J = se.retrieveSchema({ [Ze]: J[Ze] }, o), C = J.type, I = J.const, B = J.default;
        }
        !C && (be in J || Ne in J) && (C = "object");
      }
      const X = I ?? B ?? qI(P, C);
      Be(b, R, X);
    }
    $(b, V.path);
  }, [o, $, v, V, le, N]), ne = fe.useCallback((P, b) => {
    if (P !== b) {
      const R = le(b, o), C = {
        ...o
      }, I = { [P]: R }, B = Object.keys(C).map((J) => ({ [I[J] || J]: C[J] })), X = Object.assign({}, ...B);
      $(X, V.path);
    }
  }, [o, $, V, le]), pe = fe.useCallback((P) => {
    $(p_, [...V.path, P]);
  }, [$, V]);
  if (!Q || H)
    try {
      const P = Object.keys(F);
      q = VT(P, x.order);
    } catch (P) {
      return D.jsxs("div", { children: [D.jsx("p", { className: "rjsf-config-error", style: { color: "red" }, children: D.jsx(Js, { options: { disableParsingRawHTML: !0 }, children: k(Le.InvalidObjectField, [c || "root", P.message]) }) }), D.jsx("pre", { children: JSON.stringify(N) })] });
    }
  const Z = ke("ObjectFieldTemplate", v, x), ae = Q ? D.jsx(T, { ...e, fieldPathId: V, schema: N }) : void 0, z = {
    // getDisplayLabel() always returns false for object types, so just check the `uiOptions.label`
    title: x.label === !1 ? "" : U,
    description: x.label === !1 ? void 0 : G,
    properties: q.map((P) => {
      const b = Ae(N, [Me, P, Fr]), R = b ? i.additionalProperties : i[P], C = Ee(R).widget === "hidden";
      return {
        content: D.jsx(GI, { propertyName: P, required: HI(N, P), schema: re(N, [Me, P], {}), uiSchema: R, errorSchema: re(a, [P]), fieldPathId: V, formData: re(o, [P]), handleKeyRename: ne, handleRemoveProperty: pe, addedByAdditionalProperties: b, onChange: $, onBlur: h, onFocus: S, registry: v, disabled: d, readonly: m, hideError: y }, P),
        name: P,
        readonly: m,
        disabled: d,
        required: f,
        hidden: C
      };
    }),
    readonly: m,
    disabled: d,
    required: f,
    fieldPathId: l,
    uiSchema: i,
    errorSchema: a,
    schema: N,
    formData: o,
    registry: v,
    optionalDataControl: ae,
    className: Q ? "rjsf-optional-object-field" : void 0
  };
  return D.jsx(Z, { ...z, onAddProperty: ie });
}
function QI(e) {
  const { schema: t, uiSchema: i = {}, formData: o, disabled: a = !1, readonly: l = !1, onChange: c, errorSchema: f, fieldPathId: d, registry: m } = e, { globalUiOptions: y = {}, schemaUtils: h, translateString: S } = m, $ = Ee(i, y), v = ke("OptionalDataControlsTemplate", m, $), w = $o(o);
  let _, E, k, j;
  if (a || l)
    _ = df(d, "Msg"), E = w ? void 0 : S(Le.OptionalObjectEmptyMsg);
  else {
    const T = w ? Le.OptionalObjectRemove : Le.OptionalObjectAdd;
    E = S(T), w ? (_ = df(d, "Remove"), j = () => c(void 0, d.path, f)) : (_ = df(d, "Add"), k = () => {
      let N = h.getDefaultFormState(t, o, "excludeObjectChildren");
      N === void 0 && (N = En(t) === "array" ? [] : {}), c(N, d.path, f);
    });
  }
  return E && D.jsx(v, { id: _, registry: m, schema: t, uiSchema: i, label: E, onAddClick: k, onRemoveClick: j });
}
const JI = {
  array: "ArrayField",
  boolean: "BooleanField",
  integer: "NumberField",
  number: "NumberField",
  object: "ObjectField",
  string: "StringField",
  null: "NullField"
};
function XI(e, t, i) {
  const o = t.field, { fields: a } = i;
  if (typeof o == "function")
    return o;
  if (typeof o == "string" && o in a)
    return a[o];
  const l = En(e), c = Array.isArray(l) ? l[0] : l || "", f = e.$id;
  let d = JI[c];
  return f && f in a && (d = f), !d && (e.anyOf || e.oneOf) ? () => null : d in a ? a[d] : a.FallbackField;
}
function ZI(e) {
  const { schema: t, fieldPathId: i, uiSchema: o, formData: a, errorSchema: l, name: c, onChange: f, onKeyRename: d, onKeyRenameBlur: m, onRemoveProperty: y, required: h = !1, registry: S, wasPropertyKeyModified: $ = !1 } = e, { schemaUtils: v, globalFormOptions: w, globalUiOptions: _, fields: E } = S, { AnyOfField: k, OneOfField: j } = E, T = Ee(o, _), N = ke("FieldTemplate", S, T), x = ke("DescriptionFieldTemplate", S, T), F = ke("FieldHelpTemplate", S, T), V = ke("FieldErrorTemplate", S, T), U = v.retrieveSchema(t, a), G = i[Ke], Q = fe.useCallback((et, Wt, Pt, Wn) => f(et, Wt, Pt, Wn || G), [G, f]), H = XI(U, T, S), q = !!(T.disabled ?? e.disabled), le = !!(T.readonly ?? (e.readonly || e.schema.readOnly || U.readOnly)), ie = T.hideError, ne = ie === void 0 ? e.hideError : !!ie, pe = !!(T.autofocus ?? e.autofocus);
  if (Object.keys(U).length === 0)
    return null;
  let Z = v.getDisplayLabel(U, o, _);
  const ae = T.field && T.fieldReplacesAnyOrOneOf === !0;
  let z, P, b = { fieldPathId: i };
  if ((be in U || Ne in U) && !ae && !v.isSelect(U)) {
    U[be] ? (z = k, P = U[be].map((Pt) => v.retrieveSchema(Fe(Pt) ? Pt : {}, a))) : U[Ne] && (z = j, P = U[Ne].map((Pt) => v.retrieveSchema(Fe(Pt) ? Pt : {}, a)));
    const et = Qs(S, U, h, o), Wt = $o(a);
    Z = Z && (!et || Wt), b = {
      childFieldPathId: i,
      // The main FieldComponent will add `XxxOf` onto the fieldPathId to avoid duplication with the rendering of the
      // same FieldComponent by the `XxxOfField`
      fieldPathId: ln("XxxOf", w, i)
    };
  }
  const { __errors: R, ...C } = l || {}, I = Fs(o, ["ui:classNames", "classNames", "ui:style"]);
  Rr in I && (I[Rr] = Fs(I[Rr], ["classNames", "style"]));
  const B = D.jsx(H, { ...e, onChange: Q, ...b, schema: U, uiSchema: I, disabled: q, readonly: le, hideError: ne, autofocus: pe, errorSchema: C, rawErrors: R }), X = i[Ke];
  let J;
  $ ? J = c : J = Fr in U ? c : T.title || e.schema.title || U.title || e.title || c;
  const se = T.description || e.schema.description || U.description || "", ce = T.help, $e = T.widget === "hidden", nt = ["rjsf-field", `rjsf-field-${En(U)}`];
  !ne && R && R.length > 0 && nt.push("rjsf-field-error"), T.classNames && nt.push(T.classNames);
  const ot = D.jsx(F, { help: ce, fieldPathId: i, schema: U, uiSchema: o, hasErrors: !ne && R && R.length > 0, registry: S }), ze = ne || z && !v.isSelect(U) ? void 0 : D.jsx(V, { errors: R, errorSchema: l, fieldPathId: i, schema: U, uiSchema: o, registry: S }), Rt = {
    description: D.jsx(x, { id: Ys(X), description: se, schema: U, uiSchema: o, registry: S }),
    rawDescription: se,
    help: ot,
    rawHelp: typeof ce == "string" ? ce : void 0,
    errors: ze,
    rawErrors: ne ? void 0 : R,
    id: X,
    label: J,
    hidden: $e,
    onChange: f,
    onKeyRename: d,
    onKeyRenameBlur: m,
    onRemoveProperty: y,
    required: h,
    disabled: q,
    readonly: le,
    hideError: ne,
    displayLabel: Z,
    classNames: nt.join(" ").trim(),
    style: T.style,
    formData: a,
    schema: U,
    uiSchema: o,
    registry: S
  };
  return D.jsx(N, { ...Rt, children: D.jsxs(D.Fragment, { children: [B, z && D.jsx(z, { name: c, disabled: q, readonly: le, hideError: ne, errorSchema: l, formData: a, fieldPathId: i, onBlur: e.onBlur, onChange: e.onChange, onFocus: e.onFocus, options: P, registry: S, required: h, schema: U, uiSchema: o })] }) });
}
class ej extends fe.Component {
  shouldComponentUpdate(t) {
    const { registry: { globalFormOptions: i } } = this.props, { experimental_componentUpdateStrategy: o = "customDeep" } = i;
    return Q0(this, t, this.state, o);
  }
  render() {
    return D.jsx(ZI, { ...this.props });
  }
}
function tj(e) {
  const { schema: t, name: i, uiSchema: o, fieldPathId: a, formData: l, required: c, disabled: f = !1, readonly: d = !1, autofocus: m = !1, onChange: y, onBlur: h, onFocus: S, registry: $, rawErrors: v, hideError: w, title: _ } = e, { title: E, format: k } = t, { widgets: j, schemaUtils: T, globalUiOptions: N } = $, x = T.isSelect(t) ? yo(t, o) : void 0;
  let F = x ? "select" : "text";
  k && MT(t, k, j) && (F = k);
  const { widget: V = F, placeholder: U = "", title: G, ...Q } = Ee(o), H = T.getDisplayLabel(t, o, N), q = G ?? _ ?? E ?? i, le = Vn(t, V, j), ie = fe.useCallback((ne, pe, Z) => y(ne, a.path, pe, Z), [y, a]);
  return D.jsx(le, { options: { ...Q, enumOptions: x }, schema: t, uiSchema: o, id: a.$id, name: i, label: q, hideLabel: !H, hideError: w, value: l, onChange: ie, onBlur: h, onFocus: S, required: c, disabled: f, readonly: d, autofocus: m, registry: $, placeholder: U, rawErrors: v, htmlName: a.name });
}
function nj(e) {
  const { formData: t, onChange: i, fieldPathId: o } = e;
  return fe.useEffect(() => {
    t === void 0 && i(null, o.path);
  }, [o, t, i]), null;
}
function rj() {
  return {
    AnyOfField: Eg,
    ArrayField: fN,
    // ArrayField falls back to SchemaField if ArraySchemaField is not defined, which it isn't by default
    BooleanField: dN,
    FallbackField: yN,
    LayoutGridField: xd,
    LayoutHeaderField: RN,
    LayoutMultiSchemaField: DN,
    NumberField: UN,
    ObjectField: YI,
    OneOfField: Eg,
    OptionalDataControlsField: QI,
    SchemaField: ej,
    StringField: tj,
    NullField: nj
  };
}
function ij(e) {
  const { fieldPathId: t, description: i, registry: o, schema: a, uiSchema: l } = e, c = Ee(l, o.globalUiOptions), { label: f = !0 } = c;
  if (!i || !f)
    return null;
  const d = ke("DescriptionFieldTemplate", o, c);
  return D.jsx(d, { id: Ys(t), description: i, schema: a, uiSchema: l, registry: o });
}
function oj(e) {
  const { children: t, className: i, buttonsProps: o, displayLabel: a, hasDescription: l, hasToolbar: c, registry: f, uiSchema: d } = e, m = Ee(d), y = ke("ArrayFieldItemButtonsTemplate", f, m), h = {
    flex: 1,
    paddingLeft: 6,
    paddingRight: 6,
    fontWeight: "bold"
  }, S = l ? 31 : 9, $ = { display: "flex", alignItems: a ? "center" : "baseline" }, v = { display: "flex", justifyContent: "flex-end", marginTop: a ? `${S}px` : 0 };
  return D.jsxs("div", { className: i, style: $, children: [D.jsx("div", { className: c ? "col-xs-9 col-md-10 col-xl-11" : "col-xs-12", children: t }), c && D.jsx("div", { className: "col-xs-3 col-md-2 col-xl-1 array-item-toolbox", children: D.jsx("div", { className: "btn-group", style: v, children: D.jsx(y, { ...o, style: h }) }) })] });
}
function sj(e) {
  const { disabled: t, hasCopy: i, hasMoveDown: o, hasMoveUp: a, hasRemove: l, fieldPathId: c, onCopyItem: f, onRemoveItem: d, onMoveDownItem: m, onMoveUpItem: y, readonly: h, registry: S, uiSchema: $ } = e, { CopyButton: v, MoveDownButton: w, MoveUpButton: _, RemoveButton: E } = S.templates.ButtonTemplates;
  return D.jsxs(D.Fragment, { children: [(a || o) && D.jsx(_, { id: pi(c, "moveUp"), className: "rjsf-array-item-move-up", disabled: t || h || !a, onClick: y, uiSchema: $, registry: S }), (a || o) && D.jsx(w, { id: pi(c, "moveDown"), className: "rjsf-array-item-move-down", disabled: t || h || !o, onClick: m, uiSchema: $, registry: S }), i && D.jsx(v, { id: pi(c, "copy"), className: "rjsf-array-item-copy", disabled: t || h, onClick: f, uiSchema: $, registry: S }), l && D.jsx(E, { id: pi(c, "remove"), className: "rjsf-array-item-remove", disabled: t || h, onClick: d, uiSchema: $, registry: S })] });
}
function aj(e) {
  const { canAdd: t, className: i, disabled: o, fieldPathId: a, uiSchema: l, items: c, optionalDataControl: f, onAddClick: d, readonly: m, registry: y, required: h, schema: S, title: $ } = e, v = Ee(l), w = ke("ArrayFieldDescriptionTemplate", y, v), _ = ke("ArrayFieldTitleTemplate", y, v), E = !m && !o, { ButtonTemplates: { AddButton: k } } = y.templates;
  return D.jsxs("fieldset", { className: i, id: a.$id, children: [D.jsx(_, { fieldPathId: a, title: v.title || $, required: h, schema: S, uiSchema: l, registry: y, optionalDataControl: E ? f : void 0 }), D.jsx(w, { fieldPathId: a, description: v.description || S.description, schema: S, uiSchema: l, registry: y }), E ? void 0 : f, D.jsx("div", { className: "row array-item-list", children: c }), t && D.jsx(k, { id: pi(a, "add"), className: "rjsf-array-item-add", onClick: d, disabled: o || m, uiSchema: l, registry: y })] });
}
function lj(e) {
  const { fieldPathId: t, title: i, schema: o, uiSchema: a, required: l, registry: c, optionalDataControl: f } = e, d = Ee(a, c.globalUiOptions), { label: m = !0 } = d;
  if (!i || !m)
    return null;
  const y = ke("TitleFieldTemplate", c, d);
  return D.jsx(y, { id: Nd(t), title: i, required: l, schema: o, uiSchema: a, registry: c, optionalDataControl: f });
}
function uj(e) {
  const {
    id: t,
    name: i,
    // remove this from ...rest
    htmlName: o,
    value: a,
    readonly: l,
    disabled: c,
    autofocus: f,
    onBlur: d,
    onFocus: m,
    onChange: y,
    onChangeOverride: h,
    options: S,
    schema: $,
    uiSchema: v,
    registry: w,
    rawErrors: _,
    type: E,
    hideLabel: k,
    // remove this from ...rest
    hideError: j,
    // remove this from ...rest
    ...T
  } = e;
  if (!t)
    throw console.log("No id for", e), new Error(`no id for props ${JSON.stringify(e)}`);
  const N = {
    ...T,
    ...NT($, E, S)
  };
  let x;
  N.type === "number" || N.type === "integer" ? x = a || a === 0 ? a : "" : x = a ?? "";
  const F = fe.useCallback(({ target: { value: G } }) => y(G === "" ? S.emptyValue : G), [y, S]), V = fe.useCallback(({ target: G }) => d(t, G && G.value), [d, t]), U = fe.useCallback(({ target: G }) => m(t, G && G.value), [m, t]);
  return D.jsxs(D.Fragment, { children: [D.jsx("input", { id: t, name: o || t, className: "form-control", readOnly: l, disabled: c, autoFocus: f, value: x, ...N, list: $.examples ? Mf(t) : void 0, onChange: h || F, onBlur: V, onFocus: U, "aria-describedby": Pi(t, !!$.examples) }), Array.isArray($.examples) && D.jsx("datalist", { id: Mf(t), children: $.examples.concat($.default && !$.examples.includes($.default) ? [$.default] : []).map((G) => D.jsx("option", { value: G }, G)) }, `datalist_${t}`)] });
}
function cj({ uiSchema: e }) {
  const { submitText: t, norender: i, props: o = {} } = IT(e);
  return i ? null : D.jsx("div", { children: D.jsx("button", { type: "submit", ...o, className: `btn btn-info ${o.className || ""}`, children: t }) });
}
function gi(e) {
  const { iconType: t = "default", icon: i, className: o, uiSchema: a, registry: l, ...c } = e;
  return D.jsx("button", { type: "button", className: `btn btn-${t} ${o}`, ...c, children: D.jsx("i", { className: `glyphicon glyphicon-${i}` }) });
}
function fj(e) {
  const { registry: { translateString: t } } = e;
  return D.jsx(gi, { title: t(Le.CopyButton), ...e, icon: "copy" });
}
function dj(e) {
  const { registry: { translateString: t } } = e;
  return D.jsx(gi, { title: t(Le.MoveDownButton), ...e, icon: "arrow-down" });
}
function pj(e) {
  const { registry: { translateString: t } } = e;
  return D.jsx(gi, { title: t(Le.MoveUpButton), ...e, icon: "arrow-up" });
}
function hj(e) {
  const { registry: { translateString: t } } = e;
  return D.jsx(gi, { title: t(Le.RemoveButton), ...e, iconType: "danger", icon: "remove" });
}
function mj({ id: e, className: t, onClick: i, disabled: o, registry: a }) {
  const { translateString: l } = a;
  return D.jsx("div", { className: "row", children: D.jsx("p", { className: `col-xs-4 col-sm-2 col-lg-1 col-xs-offset-8 col-sm-offset-10 col-lg-offset-11 text-right ${t}`, children: D.jsx(gi, { id: e, iconType: "info", icon: "plus", className: "btn-add col-xs-12", title: l(Le.AddButton), onClick: i, disabled: o, registry: a }) }) });
}
function yj() {
  return {
    SubmitButton: cj,
    AddButton: mj,
    CopyButton: fj,
    MoveDownButton: dj,
    MoveUpButton: pj,
    RemoveButton: hj
  };
}
const h_ = Td();
function m_({ description: e, registry: t, uiSchema: i = {} }) {
  const { globalUiOptions: o } = t;
  return Ee(i, o).enableMarkdownInDescription && typeof e == "string" ? D.jsx(Js, { options: { disableParsingRawHTML: !0 }, "data-testid": h_.markdown, children: e }) : e;
}
m_.TEST_IDS = h_;
function gj(e) {
  const { id: t, description: i, registry: o, uiSchema: a } = e;
  return i ? D.jsx("div", { id: t, className: "field-description", children: D.jsx(m_, { description: i, registry: o, uiSchema: a }) }) : null;
}
function vj({ errors: e, registry: t }) {
  const { translateString: i } = t;
  return D.jsxs("div", { className: "panel panel-danger errors", children: [D.jsx("div", { className: "panel-heading", children: D.jsx("h3", { className: "panel-title", children: i(Le.ErrorsLabel) }) }), D.jsx("ul", { className: "list-group", children: e.map((o, a) => D.jsx("li", { className: "list-group-item text-danger", children: o.stack }, a)) })] });
}
function _j(e) {
  const { schema: t, registry: i, typeSelector: o, schemaField: a } = e, l = ke("MultiSchemaFieldTemplate", i);
  return D.jsx(l, { selector: o, optionSchemaField: a, schema: t, registry: i });
}
const Sj = "*";
function y_(e) {
  const { label: t, required: i, id: o } = e;
  return t ? D.jsxs("label", { className: "control-label", htmlFor: o, children: [t, i && D.jsx("span", { className: "required", children: Sj })] }) : null;
}
function wj(e) {
  const { id: t, label: i, children: o, errors: a, help: l, description: c, hidden: f, required: d, displayLabel: m, registry: y, uiSchema: h } = e, S = Ee(h), $ = ke("WrapIfAdditionalTemplate", y, S);
  if (f)
    return D.jsx("div", { className: "hidden", children: o });
  const v = S.widget === "checkbox";
  return D.jsxs($, { ...e, children: [m && !v && D.jsx(y_, { label: i, required: d, id: t }), m && c ? c : null, o, a, l] });
}
function Ej(e) {
  const { errors: t = [], fieldPathId: i } = e;
  if (t.length === 0)
    return null;
  const o = q0(i);
  return D.jsx("div", { children: D.jsx("ul", { id: o, className: "error-detail bs-callout bs-callout-info", children: t.filter((a) => !!a).map((a, l) => D.jsx("li", { className: "text-danger", children: a }, l)) }) });
}
const g_ = Td();
function v_({ help: e, registry: t, uiSchema: i = {} }) {
  const { globalUiOptions: o } = t;
  return Ee(i, o).enableMarkdownInHelp && typeof e == "string" ? D.jsx(Js, { options: { disableParsingRawHTML: !0 }, "data-testid": g_.markdown, children: e }) : e;
}
v_.TEST_IDS = g_;
function $j(e) {
  const { fieldPathId: t, help: i, uiSchema: o, registry: a } = e;
  return i ? D.jsx("div", { id: G0(t), className: "help-block", children: D.jsx(v_, { help: i, registry: a, uiSchema: o }) }) : null;
}
function Oj(e) {
  const { children: t, column: i, className: o, ...a } = e;
  return D.jsx("div", { className: o, ...a, children: t });
}
function Pj(e) {
  const { selector: t, optionSchemaField: i } = e;
  return D.jsxs("div", { className: "panel panel-default panel-body", children: [D.jsx("div", { className: "form-group", children: t }), i] });
}
function Cj(e) {
  const { className: t, description: i, disabled: o, formData: a, fieldPathId: l, onAddProperty: c, optionalDataControl: f, properties: d, readonly: m, registry: y, required: h, schema: S, title: $, uiSchema: v } = e, w = Ee(v), _ = ke("TitleFieldTemplate", y, w), E = ke("DescriptionFieldTemplate", y, w), k = !m && !o, { ButtonTemplates: { AddButton: j } } = y.templates;
  return D.jsxs("fieldset", { className: t, id: l.$id, children: [$ && D.jsx(_, { id: Nd(l), title: $, required: h, schema: S, uiSchema: v, registry: y, optionalDataControl: k ? f : void 0 }), i && D.jsx(E, { id: Ys(l), description: i, schema: S, uiSchema: v, registry: y }), k ? void 0 : f, d.map((T) => T.content), $1(S, v, a) && D.jsx(j, { id: pi(l, "add"), className: "rjsf-object-property-expand", onClick: c, disabled: o || m, uiSchema: v, registry: y })] });
}
function kj(e) {
  const { id: t, registry: i, label: o, onAddClick: a, onRemoveClick: l } = e;
  return a ? D.jsx(gi, { id: t, registry: i, icon: "plus", className: "rjsf-add-optional-data btn-sm", onClick: a, title: o }) : l ? D.jsx(gi, { id: t, registry: i, icon: "remove", className: "rjsf-remove-optional-data btn-sm", onClick: l, title: o }) : D.jsx("em", { id: t, children: o });
}
const Tj = "*";
function Nj(e) {
  const { id: t, title: i, required: o, optionalDataControl: a } = e;
  return D.jsxs("legend", { id: t, children: [i, o && D.jsx("span", { className: "required", children: Tj }), a && D.jsx("span", { className: "pull-right", style: { marginBottom: "2px" }, children: a })] });
}
function Ij(e) {
  const { schema: t, fieldPathId: i, reason: o, registry: a } = e, { translateString: l } = a;
  let c = Le.UnsupportedField;
  const f = [];
  return i && i.$id && (c = Le.UnsupportedFieldWithId, f.push(i.$id)), o && (c = c === Le.UnsupportedField ? Le.UnsupportedFieldWithReason : Le.UnsupportedFieldWithIdAndReason, f.push(o)), D.jsxs("div", { className: "unsupported-field", children: [D.jsx("p", { children: D.jsx(Js, { options: { disableParsingRawHTML: !0 }, children: l(c, f) }) }), t && D.jsx("pre", { children: JSON.stringify(t, null, 2) })] });
}
function jj(e) {
  const { id: t, classNames: i, style: o, disabled: a, displayLabel: l, label: c, onKeyRenameBlur: f, onRemoveProperty: d, rawDescription: m, readonly: y, required: h, schema: S, hideError: $, rawErrors: v, children: w, uiSchema: _, registry: E } = e, { templates: k, translateString: j } = E, { RemoveButton: T } = k.ButtonTemplates, N = j(Le.KeyLabel, [c]), x = Fr in S, F = !!m, V = ["form-group", i];
  !$ && v && v.length > 0 && V.push("has-error has-danger");
  const U = V.join(" ").trim();
  if (!x)
    return D.jsx("div", { className: U, style: o, children: w });
  const G = F ? 46 : 26;
  return D.jsx("div", { className: U, style: o, children: D.jsxs("div", { className: "row", children: [D.jsx("div", { className: "col-xs-5 form-additional", children: D.jsxs("div", { className: "form-group", children: [l && D.jsx(y_, { label: N, required: h, id: `${t}-key` }), l && m && D.jsx("div", { children: " " }), D.jsx("input", { className: "form-control", type: "text", id: `${t}-key`, onBlur: f, defaultValue: c })] }) }), D.jsx("div", { className: "form-additional form-group col-xs-5", children: w }), D.jsx("div", { className: "col-xs-2", style: { marginTop: l ? `${G}px` : void 0 }, children: D.jsx(T, { id: pi(t, "remove"), className: "rjsf-object-property-remove btn-block", style: { border: "0" }, disabled: a || y, onClick: d, uiSchema: _, registry: E }) })] }) });
}
function Aj() {
  return {
    ArrayFieldDescriptionTemplate: ij,
    ArrayFieldItemTemplate: oj,
    ArrayFieldItemButtonsTemplate: sj,
    ArrayFieldTemplate: aj,
    ArrayFieldTitleTemplate: lj,
    ButtonTemplates: yj(),
    BaseInputTemplate: uj,
    DescriptionFieldTemplate: gj,
    ErrorListTemplate: vj,
    FallbackFieldTemplate: _j,
    FieldTemplate: wj,
    FieldErrorTemplate: Ej,
    FieldHelpTemplate: $j,
    GridTemplate: Oj,
    MultiSchemaFieldTemplate: Pj,
    ObjectFieldTemplate: Cj,
    OptionalDataControlsTemplate: kj,
    TitleFieldTemplate: Nj,
    UnsupportedFieldTemplate: Ij,
    WrapIfAdditionalTemplate: jj
  };
}
function xj(e) {
  const { disabled: t = !1, readonly: i = !1, autofocus: o = !1, options: a, id: l, name: c, registry: f, onBlur: d, onFocus: m } = e, { translateString: y } = f, { elements: h, handleChange: S, handleClear: $, handleSetNow: v } = HT(e);
  return D.jsxs("ul", { className: "list-inline", children: [h.map((w, _) => D.jsx("li", { className: "list-inline-item", children: D.jsx(WT, { rootId: l, name: c, select: S, ...w, disabled: t, readonly: i, registry: f, onBlur: d, onFocus: m, autofocus: o && _ === 0 }) }, _)), (a.hideNowButton !== "undefined" ? !a.hideNowButton : !0) && D.jsx("li", { className: "list-inline-item", children: D.jsx("a", { href: "#", className: "btn btn-info btn-now", onClick: v, children: y(Le.NowLabel) }) }), (a.hideClearButton !== "undefined" ? !a.hideClearButton : !0) && D.jsx("li", { className: "list-inline-item", children: D.jsx("a", { href: "#", className: "btn btn-warning btn-clear", onClick: $, children: y(Le.ClearLabel) }) })] });
}
function bj({ time: e = !0, ...t }) {
  const { AltDateWidget: i } = t.registry.widgets;
  return D.jsx(i, { time: e, ...t });
}
function Fj({ schema: e, uiSchema: t, options: i, id: o, value: a, disabled: l, readonly: c, label: f, hideLabel: d, autofocus: m = !1, onBlur: y, onFocus: h, onChange: S, registry: $, htmlName: v }) {
  const w = ke("DescriptionFieldTemplate", $, i), _ = $l(e), E = fe.useCallback((F) => S(F.target.checked), [S]), k = fe.useCallback((F) => y(o, F.target.checked), [y, o]), j = fe.useCallback((F) => h(o, F.target.checked), [h, o]), x = Ee(t).widget === "checkbox" ? void 0 : i.description ?? e.description;
  return D.jsxs("div", { className: `checkbox ${l || c ? "disabled" : ""}`, children: [!d && x && D.jsx(w, { id: Ys(o), description: x, schema: e, uiSchema: t, registry: $ }), D.jsxs("label", { children: [D.jsx("input", { type: "checkbox", id: o, name: v || o, checked: typeof a > "u" ? !1 : a, required: _, disabled: l || c, autoFocus: m, onChange: E, onBlur: k, onFocus: j, "aria-describedby": Pi(o) }), UT(D.jsx("span", { children: f }), d)] })] });
}
function Rj({ id: e, disabled: t, options: { inline: i = !1, enumOptions: o, enumDisabled: a, emptyValue: l }, value: c, autofocus: f = !1, readonly: d, onChange: m, onBlur: y, onFocus: h, htmlName: S }) {
  const $ = Array.isArray(c) ? c : [c], v = fe.useCallback(({ target: _ }) => y(e, Un(_ && _.value, o, l)), [y, e, o, l]), w = fe.useCallback(({ target: _ }) => h(e, Un(_ && _.value, o, l)), [h, e, o, l]);
  return D.jsx("div", { className: "checkboxes", id: e, children: Array.isArray(o) && o.map((_, E) => {
    const k = Cd(_.value, $), j = Array.isArray(a) && a.indexOf(_.value) !== -1, T = t || j || d ? "disabled" : "", N = (F) => {
      F.target.checked ? m(_T(E, $, o)) : m(gT(E, $, o));
    }, x = D.jsxs("span", { children: [D.jsx("input", { type: "checkbox", id: Y0(e, E), name: S || e, checked: k, value: String(E), disabled: t || j || d, autoFocus: f && E === 0, onChange: N, onBlur: v, onFocus: w, "aria-describedby": Pi(e) }), D.jsx("span", { children: _.label })] });
    return i ? D.jsx("label", { className: `checkbox-inline ${T}`, children: x }, E) : D.jsx("div", { className: `checkbox ${T}`, children: D.jsx("label", { children: x }) }, E);
  }) });
}
function Dj(e) {
  const { disabled: t, readonly: i, options: o, registry: a } = e, l = ke("BaseInputTemplate", a, o);
  return D.jsx(l, { type: "color", ...e, disabled: t || i });
}
function Mj(e) {
  const { onChange: t, options: i, registry: o } = e, a = ke("BaseInputTemplate", o, i), l = fe.useCallback((c) => t(c || void 0), [t]);
  return D.jsx(a, { type: "date", ...e, onChange: l });
}
function Lj(e) {
  const { onChange: t, value: i, options: o, registry: a } = e, l = ke("BaseInputTemplate", a, o);
  return D.jsx(l, { type: "datetime-local", ...e, value: JT(i), onChange: (c) => t(zT(c)) });
}
function Uj(e) {
  const { options: t, registry: i } = e, o = ke("BaseInputTemplate", i, t);
  return D.jsx(o, { type: "email", ...e });
}
function zj({ fileInfo: e, registry: t }) {
  const { translateString: i } = t, { dataURL: o, type: a, name: l } = e;
  return o ? ["image/jpeg", "image/png"].includes(a) ? D.jsx("img", { src: o, style: { maxWidth: "100%" }, className: "file-preview" }) : D.jsxs(D.Fragment, { children: [" ", D.jsx("a", { download: `preview-${l}`, href: o, className: "file-download", children: i(Le.PreviewLabel) })] }) : null;
}
function Vj({ filesInfo: e, registry: t, preview: i, onRemove: o, options: a }) {
  if (e.length === 0)
    return null;
  const { translateString: l } = t, { RemoveButton: c } = ke("ButtonTemplates", t, a);
  return D.jsx("ul", { className: "file-info", children: e.map((f, d) => {
    const { name: m, size: y, type: h } = f, S = () => o(d);
    return D.jsxs("li", { children: [D.jsx(Js, { children: l(Le.FilesInfo, [m, h, String(y)]) }), i && D.jsx(zj, { fileInfo: f, registry: t }), D.jsx(c, { onClick: S, registry: t })] }, d);
  }) });
}
function Bj(e) {
  const { disabled: t, readonly: i, required: o, multiple: a, onChange: l, value: c, options: f, registry: d } = e, { filesInfo: m, handleChange: y, handleRemove: h } = QT(c, l, a), S = ke("BaseInputTemplate", d, f), $ = (v) => {
    v.target.files && y(v.target.files);
  };
  return D.jsxs("div", { children: [D.jsx(S, { ...e, disabled: t || i, type: "file", required: c ? !1 : o, onChangeOverride: $, value: "", accept: f.accept ? String(f.accept) : void 0 }), D.jsx(Vj, { filesInfo: m, onRemove: h, registry: d, preview: f.filePreview, options: f })] });
}
function Kj({ id: e, value: t, htmlName: i }) {
  return D.jsx("input", { type: "hidden", id: e, name: i || e, value: typeof t > "u" ? "" : t });
}
function Wj(e) {
  const { options: t, registry: i } = e, o = ke("BaseInputTemplate", i, t);
  return D.jsx(o, { type: "password", ...e });
}
function Hj({ options: e, value: t, required: i, disabled: o, readonly: a, autofocus: l = !1, onBlur: c, onFocus: f, onChange: d, id: m, htmlName: y }) {
  const { enumOptions: h, enumDisabled: S, inline: $, emptyValue: v } = e, w = fe.useCallback(({ target: E }) => c(m, Un(E && E.value, h, v)), [c, h, v, m]), _ = fe.useCallback(({ target: E }) => f(m, Un(E && E.value, h, v)), [f, h, v, m]);
  return D.jsx("div", { className: "field-radio-group", id: m, role: "radiogroup", children: Array.isArray(h) && h.map((E, k) => {
    const j = Cd(E.value, t), T = Array.isArray(S) && S.indexOf(E.value) !== -1, N = o || T || a ? "disabled" : "", x = () => d(E.value), F = D.jsxs("span", { children: [D.jsx("input", { type: "radio", id: Y0(m, k), checked: j, name: y || m, required: i, value: String(k), disabled: o || T || a, autoFocus: l && k === 0, onChange: x, onBlur: w, onFocus: _, "aria-describedby": Pi(m) }), D.jsx("span", { children: E.label })] });
    return $ ? D.jsx("label", { className: `radio-inline ${N}`, children: F }, k) : D.jsx("div", { className: `radio ${N}`, children: D.jsx("label", { children: F }) }, k);
  }) });
}
function qj(e) {
  const { value: t, registry: { templates: { BaseInputTemplate: i } } } = e;
  return D.jsxs("div", { className: "field-range-wrapper", children: [D.jsx(i, { type: "range", ...e }), D.jsx("span", { className: "range-view", children: t })] });
}
function Gj({ id: e, value: t, required: i, disabled: o, readonly: a, autofocus: l, onChange: c, onFocus: f, onBlur: d, schema: m, options: y, htmlName: h }) {
  const { stars: S = 5, shape: $ = "star" } = y, v = m.maximum ? Math.min(m.maximum, 5) : Math.min(Math.max(S, 1), 5), w = m.minimum || 0, _ = fe.useCallback((T) => {
    !o && !a && c(T);
  }, [c, o, a]), E = fe.useCallback((T) => {
    if (f) {
      const N = Number(T.target.dataset.value);
      f(e, N);
    }
  }, [f, e]), k = fe.useCallback((T) => {
    if (d) {
      const N = Number(T.target.dataset.value);
      d(e, N);
    }
  }, [d, e]), j = (T) => $ === "heart" ? T ? "♥" : "♡" : T ? "★" : "☆";
  return D.jsx(D.Fragment, { children: D.jsxs("div", { className: "rating-widget", style: {
    display: "inline-flex",
    fontSize: "1.5rem",
    cursor: o || a ? "default" : "pointer"
  }, children: [[...Array(v)].map((T, N) => {
    const x = w + N, F = x <= t;
    return D.jsx("span", { onClick: () => _(x), onFocus: E, onBlur: k, "data-value": x, tabIndex: o || a ? -1 : 0, role: "radio", "aria-checked": x === t, "aria-label": `${x} ${$ === "heart" ? "heart" : "star"}${x === 1 ? "" : "s"}`, style: {
      color: F ? "#FFD700" : "#ccc",
      padding: "0 0.2rem",
      transition: "color 0.2s",
      userSelect: "none"
    }, children: j(F) }, N);
  }), D.jsx("input", { type: "hidden", id: e, name: h || e, value: t || "", required: i, disabled: o || a, "aria-hidden": "true" })] }) });
}
function _f(e, t) {
  return t ? Array.from(e.target.options).slice().filter((i) => i.selected).map((i) => i.value) : e.target.value;
}
function Yj({ schema: e, id: t, options: i, value: o, required: a, disabled: l, readonly: c, multiple: f = !1, autofocus: d = !1, onChange: m, onBlur: y, onFocus: h, placeholder: S, htmlName: $ }) {
  const { enumOptions: v, enumDisabled: w, emptyValue: _ } = i, E = f ? [] : "", k = fe.useCallback((F) => {
    const V = _f(F, f);
    return h(t, Un(V, v, _));
  }, [h, t, f, v, _]), j = fe.useCallback((F) => {
    const V = _f(F, f);
    return y(t, Un(V, v, _));
  }, [y, t, f, v, _]), T = fe.useCallback((F) => {
    const V = _f(F, f);
    return m(Un(V, v, _));
  }, [m, f, v, _]), N = vT(o, v, f), x = !f && e.default === void 0;
  return D.jsxs("select", { id: t, name: $ || t, multiple: f, role: "combobox", className: "form-control", value: typeof N > "u" ? E : N, required: a, disabled: l || c, autoFocus: d, onBlur: j, onFocus: k, onChange: T, "aria-describedby": Pi(t), children: [x && D.jsx("option", { value: "", children: S }), Array.isArray(v) && v.map(({ value: F, label: V }, U) => {
    const G = w && w.indexOf(F) !== -1;
    return D.jsx("option", { value: String(U), disabled: G, children: V }, U);
  })] });
}
function __({ id: e, options: t = {}, placeholder: i, value: o, required: a, disabled: l, readonly: c, autofocus: f = !1, onChange: d, onBlur: m, onFocus: y, htmlName: h }) {
  const S = fe.useCallback(({ target: { value: w } }) => d(w === "" ? t.emptyValue : w), [d, t.emptyValue]), $ = fe.useCallback(({ target: w }) => m(e, w && w.value), [m, e]), v = fe.useCallback(({ target: w }) => y(e, w && w.value), [e, y]);
  return D.jsx("textarea", { id: e, name: h || e, className: "form-control", value: o || "", placeholder: i, required: a, disabled: l, readOnly: c, autoFocus: f, rows: t.rows, onBlur: $, onFocus: v, onChange: S, "aria-describedby": Pi(e) });
}
__.defaultProps = {
  autofocus: !1,
  options: {}
};
function Qj(e) {
  const { options: t, registry: i } = e, o = ke("BaseInputTemplate", i, t);
  return D.jsx(o, { ...e });
}
function Jj(e) {
  const { onChange: t, options: i, registry: o } = e, a = ke("BaseInputTemplate", o, i), l = fe.useCallback((c) => t(c ? `${c}:00` : void 0), [t]);
  return D.jsx(a, { type: "time", ...e, onChange: l });
}
function Xj(e) {
  const { options: t, registry: i } = e, o = ke("BaseInputTemplate", i, t);
  return D.jsx(o, { type: "url", ...e });
}
function Zj(e) {
  const { options: t, registry: i } = e, o = ke("BaseInputTemplate", i, t);
  return D.jsx(o, { type: "number", ...e });
}
function eA() {
  return {
    AltDateWidget: xj,
    AltDateTimeWidget: bj,
    CheckboxWidget: Fj,
    CheckboxesWidget: Rj,
    ColorWidget: Dj,
    DateWidget: Mj,
    DateTimeWidget: Lj,
    EmailWidget: Uj,
    FileWidget: Bj,
    HiddenWidget: Kj,
    PasswordWidget: Wj,
    RadioWidget: Hj,
    RangeWidget: qj,
    RatingWidget: Gj,
    SelectWidget: Yj,
    TextWidget: Qj,
    TextareaWidget: __,
    TimeWidget: Jj,
    UpDownWidget: Zj,
    URLWidget: Xj
  };
}
function tA() {
  return {
    fields: rj(),
    templates: Aj(),
    widgets: eA(),
    rootSchema: {},
    formContext: {},
    translateString: yT,
    globalFormOptions: {
      idPrefix: gv,
      idSeparator: vv,
      useFallbackUiForUnsupportedType: !1
    }
  };
}
function to(e, t) {
  return {
    ...Z0(e, ["schema", "uiSchema", "fieldPathId", "schemaUtils", "formData", "edit", "errors", "errorSchema"]),
    ...t !== void 0 && { status: t }
  };
}
class nA extends fe.Component {
  /** Constructs the `Form` from the `props`. Will setup the initial state from the props. It will also call the
   * `onChange` handler if the initially provided `formData` is modified to add missing default values as part of the
   * state construction.
   *
   * @param props - The initial props for the `Form`
   */
  constructor(i) {
    super(i);
    /** The ref used to hold the `form` element, this needs to be `any` because `tagName` or `_internalFormWrapper` can
     * provide any possible type here
     */
    bt(this, "formElement");
    /** The list of pending changes
     */
    bt(this, "pendingChanges", []);
    /** Returns the `formData` with only the elements specified in the `fields` list
     *
     * @param formData - The data for the `Form`
     * @param fields - The fields to keep while filtering
     */
    bt(this, "getUsedFormData", (i, o) => {
      if (o.length === 0 && typeof i != "object")
        return i;
      const a = Z0(i, o);
      return Array.isArray(i) ? Object.keys(a).map((l) => a[l]) : a;
    });
    /** Returns the list of field names from inspecting the `pathSchema` as well as using the `formData`
     *
     * @param pathSchema - The `PathSchema` object for the form
     * @param [formData] - The form data to use while checking for empty objects/arrays
     */
    bt(this, "getFieldNames", (i, o) => {
      const a = (c, f) => typeof c != "object" || dt(c) || f && !dt(c), l = (c, f = [], d = [[]]) => {
        const m = Object.keys(c);
        return m.forEach((y) => {
          const h = c[y];
          if (typeof h == "object") {
            const S = d.map(($) => [...$, y]);
            h[Xf] && h[gl] !== "" ? f.push(h[gl]) : l(h, f, S);
          } else y === gl && h !== "" && d.forEach((S) => {
            const $ = re(o, S), v = m.length === 1;
            (a($, v) || Array.isArray($) && $.every((w) => a(w, v))) && f.push(S);
          });
        }), f;
      };
      return l(i);
    });
    /** Returns the `formData` after filtering to remove any extra data not in a form field
     *
     * @param formData - The data for the `Form`
     * @returns The `formData` after omitting extra data
     */
    bt(this, "omitExtraData", (i) => {
      const { schema: o, schemaUtils: a } = this.state, l = a.retrieveSchema(o, i), c = a.toPathSchema(l, "", i), f = this.getFieldNames(c, i);
      return this.getUsedFormData(i, f);
    });
    /** Allows a user to set a value for the provided `fieldPath`, which must be either a dotted path to the field OR a
     * `FieldPathList`. To set the root element, used either `''` or `[]` for the path. Passing undefined will clear the
     * value in the field.
     *
     * @param fieldPath - Either a dotted path to the field or the `FieldPathList` to the field
     * @param [newValue] - The new value for the field
     */
    bt(this, "setFieldValue", (i, o) => {
      const { registry: a } = this.state, l = Array.isArray(i) ? i : i.split("."), c = ln("", a.globalFormOptions, l);
      this.onChange(o, l, void 0, c[Ke]);
    });
    /** Pushes the given change information into the `pendingChanges` array and then calls `processPendingChanges()` if
     * the array only contains a single pending change.
     *
     * @param newValue - The new form data from a change to a field
     * @param path - The path to the change into which to set the formData
     * @param [newErrorSchema] - The new `ErrorSchema` based on the field change
     * @param [id] - The id of the field that caused the change
     */
    bt(this, "onChange", (i, o, a, l) => {
      this.pendingChanges.push({ newValue: i, path: o, newErrorSchema: a, id: l }), this.pendingChanges.length === 1 && this.processPendingChange();
    });
    /**
     * Callback function to handle reset form data.
     * - Reset all fields with default values.
     * - Reset validations and errors
     *
     */
    bt(this, "reset", () => {
      const { formData: i, initialFormData: o = Ug, onChange: a } = this.props, f = {
        formData: this.getStateFromProps(this.props, i ?? o, void 0, void 0, void 0, !0).formData,
        errorSchema: {},
        errors: [],
        schemaValidationErrors: [],
        schemaValidationErrorSchema: {},
        initialDefaultsGenerated: !1,
        customErrors: void 0
      };
      this.setState(f, () => a && a(to({ ...this.state, ...f })));
    });
    /** Callback function to handle when a field on the form is blurred. Calls the `onBlur` callback for the `Form` if it
     * was provided. Also runs any live validation and/or live omit operations if the flags indicate they should happen
     * during `onBlur`.
     *
     * @param id - The unique `id` of the field that was blurred
     * @param data - The data associated with the field that was blurred
     */
    bt(this, "onBlur", (i, o) => {
      const { onBlur: a, omitExtraData: l, liveOmit: c, liveValidate: f } = this.props;
      if (a && a(i, o), l === !0 && c === "onBlur" || f === "onBlur") {
        const { onChange: d, extraErrors: m } = this.props, { formData: y } = this.state;
        let h = y, S = { formData: h };
        if (l === !0 && c === "onBlur" && (h = this.omitExtraData(y), S = { formData: h }), f === "onBlur") {
          const { schema: v, schemaUtils: w, errorSchema: _, customErrors: E, retrievedSchema: k } = this.state, j = this.liveValidate(v, w, _, h, m, E, k);
          S = { formData: h, ...j, customErrors: E };
        }
        const $ = Object.keys(S).filter((v) => !v.startsWith("schemaValidation")).some((v) => {
          const w = re(this.state, v), _ = re(S, v);
          return !Ge(w, _);
        });
        this.setState(S, () => {
          d && $ && d(to({ ...this.state, ...S }), i);
        });
      }
    });
    /** Callback function to handle when a field on the form is focused. Calls the `onFocus` callback for the `Form` if it
     * was provided.
     *
     * @param id - The unique `id` of the field that was focused
     * @param data - The data associated with the field that was focused
     */
    bt(this, "onFocus", (i, o) => {
      const { onFocus: a } = this.props;
      a && a(i, o);
    });
    /** Callback function to handle when the form is submitted. First, it prevents the default event behavior. Nothing
     * happens if the target and currentTarget of the event are not the same. It will omit any extra data in the
     * `formData` in the state if `omitExtraData` is true. It will validate the resulting `formData`, reporting errors
     * via the `onError()` callback unless validation is disabled. Finally, it will add in any `extraErrors` and then call
     * back the `onSubmit` callback if it was provided.
     *
     * @param event - The submit HTML form event
     */
    bt(this, "onSubmit", (i) => {
      if (i.preventDefault(), i.target !== i.currentTarget)
        return;
      i.persist();
      const { omitExtraData: o, extraErrors: a, noValidate: l, onSubmit: c } = this.props;
      let { formData: f } = this.state;
      if (o === !0 && (f = this.omitExtraData(f)), l || this.validateFormWithFormData(f)) {
        const d = a || {}, m = a ? jd(a) : [];
        this.setState({
          formData: f,
          errors: m,
          errorSchema: d,
          schemaValidationErrors: [],
          schemaValidationErrorSchema: {}
        }, () => {
          c && c(to({ ...this.state, formData: f }, "submitted"), i);
        });
      }
    });
    /** Provides a function that can be used to programmatically submit the `Form` */
    bt(this, "submit", () => {
      if (this.formElement.current) {
        const i = new CustomEvent("submit", {
          cancelable: !0
        });
        i.preventDefault(), this.formElement.current.dispatchEvent(i), this.formElement.current.requestSubmit();
      }
    });
    /** Validates the form using the given `formData`. For use on form submission or on programmatic validation.
     * If `onError` is provided, then it will be called with the list of errors.
     *
     * @param formData - The form data to validate
     * @returns - True if the form is valid, false otherwise.
     */
    bt(this, "validateFormWithFormData", (i) => {
      const { extraErrors: o, extraErrorsBlockSubmit: a, focusOnFirstError: l, onError: c } = this.props, { errors: f } = this.state, d = this.validate(i);
      let m = d.errors, y = d.errorSchema;
      const h = m, S = y, $ = m.length > 0 || o && a;
      if ($) {
        if (o) {
          const v = Ol(d, o);
          y = v.errorSchema, m = v.errors;
        }
        l && (typeof l == "function" ? l(m[0]) : this.focusOnError(m[0])), this.setState({
          errors: m,
          errorSchema: y,
          schemaValidationErrors: h,
          schemaValidationErrorSchema: S
        }, () => {
          c ? c(m) : console.error("Form validation failed", m);
        });
      } else f.length > 0 && this.setState({
        errors: [],
        errorSchema: {},
        schemaValidationErrors: [],
        schemaValidationErrorSchema: {}
      });
      return !$;
    });
    if (!i.validator)
      throw new Error("A validator is required for Form functionality to work");
    const { formData: o, initialFormData: a, onChange: l } = i, c = o ?? a;
    this.state = this.getStateFromProps(i, c, void 0, void 0, void 0, !0), l && !Ge(this.state.formData, c) && l(to(this.state)), this.formElement = fe.createRef();
  }
  /**
   * `getSnapshotBeforeUpdate` is a React lifecycle method that is invoked right before the most recently rendered
   * output is committed to the DOM. It enables your component to capture current values (e.g., scroll position) before
   * they are potentially changed.
   *
   * In this case, it checks if the props have changed since the last render. If they have, it computes the next state
   * of the component using `getStateFromProps` method and returns it along with a `shouldUpdate` flag set to `true` IF
   * the `nextState` and `prevState` are different, otherwise `false`. This ensures that we have the most up-to-date
   * state ready to be applied in `componentDidUpdate`.
   *
   * If `formData` hasn't changed, it simply returns an object with `shouldUpdate` set to `false`, indicating that a
   * state update is not necessary.
   *
   * @param prevProps - The previous set of props before the update.
   * @param prevState - The previous state before the update.
   * @returns Either an object containing the next state and a flag indicating that an update should occur, or an object
   *        with a flag indicating that an update is not necessary.
   */
  getSnapshotBeforeUpdate(i, o) {
    if (!Ge(this.props, i)) {
      const a = ug(this.props.formData, i.formData), l = ug(this.props.formData, this.state.formData), c = !Ge(i.schema, this.props.schema), f = a.length > 0 || !Ge(i.formData, this.props.formData), d = l.length > 0 || !Ge(this.state.formData, this.props.formData), m = this.getStateFromProps(
        this.props,
        this.props.formData,
        // If the `schema` has changed, we need to update the retrieved schema.
        // Or if the `formData` changes, for example in the case of a schema with dependencies that need to
        //  match one of the subSchemas, the retrieved schema must be updated.
        c || f ? void 0 : this.state.retrievedSchema,
        c,
        a,
        // Skip live validation for this request if no form data has changed from the last state
        !d
      ), y = !Ge(m, o);
      return { nextState: m, shouldUpdate: y };
    }
    return { shouldUpdate: !1 };
  }
  /**
   * `componentDidUpdate` is a React lifecycle method that is invoked immediately after updating occurs. This method is
   * not called for the initial render.
   *
   * Here, it checks if an update is necessary based on the `shouldUpdate` flag received from `getSnapshotBeforeUpdate`.
   * If an update is required, it applies the next state and, if needed, triggers the `onChange` handler to inform about
   * changes.
   *
   * @param _ - The previous set of props.
   * @param prevState - The previous state of the component before the update.
   * @param snapshot - The value returned from `getSnapshotBeforeUpdate`.
   */
  componentDidUpdate(i, o, a) {
    if (a.shouldUpdate) {
      const { nextState: l } = a;
      !Ge(l.formData, this.props.formData) && !Ge(l.formData, o.formData) && this.props.onChange && this.props.onChange(to(l)), this.setState(l);
    }
  }
  /** Extracts the updated state from the given `props` and `inputFormData`. As part of this process, the
   * `inputFormData` is first processed to add any missing required defaults. After that, the data is run through the
   * validation process IF required by the `props`.
   *
   * @param props - The props passed to the `Form`
   * @param inputFormData - The new or current data for the `Form`
   * @param retrievedSchema - An expanded schema, if not provided, it will be retrieved from the `schema` and `formData`.
   * @param isSchemaChanged - A flag indicating whether the schema has changed.
   * @param formDataChangedFields - The changed fields of `formData`
   * @param skipLiveValidate - Optional flag, if true, means that we are not running live validation
   * @returns - The new state for the `Form`
   */
  getStateFromProps(i, o, a, l = !1, c = [], f = !1) {
    var ne;
    const d = this.state || {}, m = "schema" in i ? i.schema : this.props.schema, y = "validator" in i ? i.validator : this.props.validator, h = ("uiSchema" in i ? i.uiSchema : this.props.uiSchema) || {}, S = i.formData === void 0 && this.props.formData === void 0, $ = typeof o < "u", v = "liveValidate" in i ? i.liveValidate : this.props.liveValidate, w = $ && !i.noValidate && v, _ = "experimental_defaultFormStateBehavior" in i ? i.experimental_defaultFormStateBehavior : this.props.experimental_defaultFormStateBehavior, E = "experimental_customMergeAllOf" in i ? i.experimental_customMergeAllOf : this.props.experimental_customMergeAllOf;
    let k = d.schemaUtils;
    (!k || k.doesSchemaUtilsDiffer(y, m, _, E)) && (k = pT(y, m, _, E));
    const j = k.getRootSchema();
    let T = o;
    o === Ug ? T = void 0 : o === void 0 && S && (T = d.formData);
    const N = k.getDefaultFormState(j, T, !1, d.initialDefaultsGenerated), x = this.updateRetrievedSchema(a ?? k.retrieveSchema(j, N)), F = () => i.noValidate || l ? { errors: [], errorSchema: {} } : i.liveValidate ? {
      errors: d.errors || [],
      errorSchema: d.errorSchema || {}
    } : {
      errors: d.schemaValidationErrors || [],
      errorSchema: d.schemaValidationErrorSchema || {}
    };
    let V, U, G = d.schemaValidationErrors, Q = d.schemaValidationErrorSchema;
    if (w && !f) {
      const pe = this.liveValidate(
        j,
        k,
        d.errorSchema,
        N,
        void 0,
        d.customErrors,
        a,
        // If retrievedSchema is undefined which means the schema or formData has changed, we do not merge state.
        // Else in the case where it hasn't changed,
        a !== void 0
      );
      V = pe.errors, U = pe.errorSchema, G = pe.schemaValidationErrors, Q = pe.schemaValidationErrorSchema;
    } else {
      const pe = F();
      if (V = pe.errors, U = pe.errorSchema, c.length > 0 && !w) {
        const ae = c.reduce((z, P) => (z[P] = void 0, z), {});
        U = Q = Ls(pe.errorSchema, ae, "preventDuplicates");
      }
      const Z = this.mergeErrors({ errorSchema: U, errors: V }, i.extraErrors, d.customErrors);
      V = Z.errors, U = Z.errorSchema;
    }
    const H = this.getRegistry(i, j, k), q = Ge(d.registry, H) ? d.registry : H, le = d.fieldPathId && ((ne = d.fieldPathId) == null ? void 0 : ne[Ke]) === q.globalFormOptions.idPrefix ? d.fieldPathId : ln("", q.globalFormOptions);
    return {
      schemaUtils: k,
      schema: j,
      uiSchema: h,
      fieldPathId: le,
      formData: N,
      edit: $,
      errors: V,
      errorSchema: U,
      schemaValidationErrors: G,
      schemaValidationErrorSchema: Q,
      retrievedSchema: x,
      initialDefaultsGenerated: !0,
      registry: q
    };
  }
  /** React lifecycle method that is used to determine whether component should be updated.
   *
   * @param nextProps - The next version of the props
   * @param nextState - The next version of the state
   * @returns - True if the component should be updated, false otherwise
   */
  shouldComponentUpdate(i, o) {
    const { experimental_componentUpdateStrategy: a = "customDeep" } = this.props;
    return Q0(this, i, o, a);
  }
  /** Validates the `formData` against the `schema` using the `altSchemaUtils` (if provided otherwise it uses the
   * `schemaUtils` in the state), returning the results.
   *
   * @param formData - The new form data to validate
   * @param schema - The schema used to validate against
   * @param [altSchemaUtils] - The alternate schemaUtils to use for validation
   * @param [retrievedSchema] - An optionally retrieved schema for per
   */
  validate(i, o = this.state.schema, a, l) {
    const c = a || this.state.schemaUtils, { customValidate: f, transformErrors: d, uiSchema: m } = this.props, y = l ?? c.retrieveSchema(o, i);
    return c.getValidator().validateFormData(i, y, f, d, m);
  }
  /** Renders any errors contained in the `state` in using the `ErrorList`, if not disabled by `showErrorList`. */
  renderErrors(i) {
    const { errors: o, errorSchema: a, schema: l, uiSchema: c } = this.state, f = Ee(c), d = ke("ErrorListTemplate", i, f);
    return o && o.length ? D.jsx(d, { errors: o, errorSchema: a || {}, schema: l, uiSchema: c, registry: i }) : null;
  }
  /** Merges any `extraErrors` or `customErrors` into the given `schemaValidation` object, returning the result
   *
   * @param schemaValidation - The `ValidationData` object into which additional errors are merged
   * @param [extraErrors] - The extra errors from the props
   * @param [customErrors] - The customErrors from custom components
   * @return - The `extraErrors` and `customErrors` merged into the `schemaValidation`
   * @private
   */
  mergeErrors(i, o, a) {
    let l = i.errorSchema, c = i.errors;
    if (o) {
      const f = Ol(i, o);
      l = f.errorSchema, c = f.errors;
    }
    if (a) {
      const f = Ol(i, a.ErrorSchema, !0);
      l = f.errorSchema, c = f.errors;
    }
    return { errors: c, errorSchema: l };
  }
  /** Performs live validation and then updates and returns the errors and error schemas by potentially merging in
   * `extraErrors` and `customErrors`.
   *
   * @param rootSchema - The `rootSchema` from the state
   * @param schemaUtils - The `SchemaUtilsType` from the state
   * @param originalErrorSchema - The original `ErrorSchema` from the state
   * @param [formData] - The new form data to validate
   * @param [extraErrors] - The extra errors from the props
   * @param [customErrors] - The customErrors from custom components
   * @param [retrievedSchema] - An expanded schema, if not provided, it will be retrieved from the `schema` and `formData`
   * @param [mergeIntoOriginalErrorSchema=false] - Optional flag indicating whether we merge into original schema
   * @returns - An object containing `errorSchema`, `errors`, `schemaValidationErrors` and `schemaValidationErrorSchema`
   * @private
   */
  liveValidate(i, o, a, l, c, f, d, m = !1) {
    const y = this.validate(l, i, o, d), h = y.errors;
    let S = y.errorSchema;
    m && (S = Ls(a, y.errorSchema, "preventDuplicates"));
    const $ = h, v = S;
    return { ...this.mergeErrors({ errorSchema: S, errors: h }, c, f), schemaValidationErrors: $, schemaValidationErrorSchema: v };
  }
  /** Function to handle changes made to a field in the `Form`. This handler gets the first change from the
   * `pendingChanges` list, containing the `newValue` for the `formData` and the `path` at which the `newValue` is to be
   * updated, along with a new, optional `ErrorSchema` for that same `path` and potentially the `id` of the field being
   * changed. It will first update the `formData` with any missing default fields and then, if `omitExtraData` and
   * `liveOmit` are turned on, the `formData` will be filtered to remove any extra data not in a form field. Then, the
   * resulting `formData` will be validated if required. The state will be updated with the new updated (potentially
   * filtered) `formData`, any errors that resulted from validation. Finally the `onChange` callback will be called, if
   * specified, with the updated state and the `processPendingChange()` function is called again.
   */
  processPendingChange() {
    if (this.pendingChanges.length === 0)
      return;
    const { newValue: i, path: o, id: a } = this.pendingChanges[0], { newErrorSchema: l } = this.pendingChanges[0], { extraErrors: c, omitExtraData: f, liveOmit: d, noValidate: m, liveValidate: y, onChange: h } = this.props, { formData: S, schemaUtils: $, schema: v, fieldPathId: w, schemaValidationErrorSchema: _, errors: E } = this.state;
    let { customErrors: k, errorSchema: j } = this.state;
    const T = w.path[0] || "", N = !o || o.length === 0 || o.length === 1 && o[0] === T;
    let x = this.state.retrievedSchema, F = N ? i : kd(S);
    if (xe(F) || Array.isArray(F)) {
      i === p_ ? nN(F, o) : N || Be(F, o, i);
      const Q = this.getStateFromProps(this.props, F, void 0, void 0, void 0, !0);
      F = Q.formData, x = Q.retrievedSchema;
    }
    const V = !m && (y === !0 || y === "onChange");
    let U = { formData: F, schema: v }, G = F;
    if (f === !0 && (d === !0 || d === "onChange") && (G = this.omitExtraData(F), U = {
      formData: G
    }), l) {
      const Q = N ? _ : re(_, o);
      if (!dt(Q))
        N ? j = l : Be(j, o, l);
      else if (k || (k = new B0()), N) {
        const H = re(l, $t);
        H && k.setErrors(H);
      } else
        Be(k.ErrorSchema, o, l);
    } else k && re(k.ErrorSchema, [...o, $t]) && k.clearErrors(o);
    if (V && this.pendingChanges.length === 1) {
      const Q = this.liveValidate(v, $, j, G, c, k, x);
      U = { formData: G, ...Q, customErrors: k };
    } else if (!m && l) {
      const Q = this.mergeErrors({ errorSchema: j, errors: E }, c, k);
      U = {
        formData: G,
        ...Q,
        customErrors: k
      };
    }
    this.setState(U, () => {
      h && h(to({ ...this.state, ...U }), a), this.pendingChanges.shift(), this.processPendingChange();
    });
  }
  /**
   * If the retrievedSchema has changed the new retrievedSchema is returned.
   * Otherwise, the old retrievedSchema is returned to persist reference.
   * -  This ensures that AJV retrieves the schema from the cache when it has not changed,
   *    avoiding the performance cost of recompiling the schema.
   *
   * @param retrievedSchema The new retrieved schema.
   * @returns The new retrieved schema if it has changed, else the old retrieved schema.
   */
  updateRetrievedSchema(i) {
    var a;
    return Ge(i, (a = this.state) == null ? void 0 : a.retrievedSchema) ? this.state.retrievedSchema : i;
  }
  /** Extracts the `GlobalFormOptions` from the given Form `props`
   *
   * @param props - The form props to extract the global form options from
   * @returns - The `GlobalFormOptions` from the props
   * @private
   */
  getGlobalFormOptions(i) {
    const { uiSchema: o = {}, experimental_componentUpdateStrategy: a, idSeparator: l = vv, idPrefix: c = gv, nameGenerator: f, useFallbackUiForUnsupportedType: d = !1 } = i;
    return {
      idPrefix: o["ui:rootFieldId"] || c,
      idSeparator: l,
      useFallbackUiForUnsupportedType: d,
      ...a !== void 0 && { experimental_componentUpdateStrategy: a },
      ...f !== void 0 && { nameGenerator: f }
    };
  }
  /** Computed the registry for the form using the given `props`, `schema` and `schemaUtils` */
  getRegistry(i, o, a) {
    var S;
    const { translateString: l, uiSchema: c = {} } = i, { fields: f, templates: d, widgets: m, formContext: y, translateString: h } = tA();
    return {
      fields: { ...f, ...i.fields },
      templates: {
        ...d,
        ...i.templates,
        ButtonTemplates: {
          ...d.ButtonTemplates,
          ...(S = i.templates) == null ? void 0 : S.ButtonTemplates
        }
      },
      widgets: { ...m, ...i.widgets },
      rootSchema: o,
      formContext: i.formContext || y,
      schemaUtils: a,
      translateString: l || h,
      globalUiOptions: c[Cf],
      globalFormOptions: this.getGlobalFormOptions(i)
    };
  }
  /** Attempts to focus on the field associated with the `error`. Uses the `property` field to compute path of the error
   * field, then, using the `idPrefix` and `idSeparator` converts that path into an id. Then the input element with that
   * id is attempted to be found using the `formElement` ref. If it is located, then it is focused.
   *
   * @param error - The error on which to focus
   */
  focusOnError(i) {
    const { idPrefix: o = "root", idSeparator: a = "_" } = this.props, { property: l } = i, c = J0(l);
    c[0] === "" ? c[0] = o : c.unshift(o);
    const f = c.join(a);
    let d = this.formElement.current.elements[f];
    d || (d = this.formElement.current.querySelector(`input[id^="${f}"`)), d && d.length && (d = d[0]), d && d.focus();
  }
  /** Programmatically validate the form.  If `omitExtraData` is true, the `formData` will first be filtered to remove
   * any extra data not in a form field. If `onError` is provided, then it will be called with the list of errors the
   * same way as would happen on form submission.
   *
   * @returns - True if the form is valid, false otherwise.
   */
  validateForm() {
    const { omitExtraData: i } = this.props;
    let { formData: o } = this.state;
    return i === !0 && (o = this.omitExtraData(o)), this.validateFormWithFormData(o);
  }
  /** Renders the `Form` fields inside the <form> | `tagName` or `_internalFormWrapper`, rendering any errors if
   * needed along with the submit button or any children of the form.
   */
  render() {
    const { children: i, id: o, className: a = "", tagName: l, name: c, method: f, target: d, action: m, autoComplete: y, enctype: h, acceptCharset: S, noHtml5Validate: $ = !1, disabled: v, readonly: w, showErrorList: _ = "top", _internalFormWrapper: E } = this.props, { schema: k, uiSchema: j, formData: T, errorSchema: N, fieldPathId: x, registry: F } = this.state, { SchemaField: V } = F.fields, { SubmitButton: U } = F.templates.ButtonTemplates, G = E ? l : void 0, Q = E || l || "form";
    let { [jl]: H = {} } = Ee(j);
    v && (H = { ...H, props: { ...H.props, disabled: !0 } });
    const q = { [Rr]: { [jl]: H } };
    return D.jsxs(Q, { className: a || "rjsf", id: o, name: c, method: f, target: d, action: m, autoComplete: y, encType: h, acceptCharset: S, noValidate: $, onSubmit: this.onSubmit, as: G, ref: this.formElement, children: [_ === "top" && this.renderErrors(F), D.jsx(V, { name: "", schema: k, uiSchema: j, errorSchema: N, fieldPathId: x, formData: T, onChange: this.onChange, onBlur: this.onBlur, onFocus: this.onFocus, registry: F, disabled: v, readonly: w }), i || D.jsx(U, { uiSchema: q, registry: F }), _ === "bottom" && this.renderErrors(F)] });
  }
}
var Vf = { exports: {} }, S_ = {}, wn = {}, vo = {}, Xs = {}, Te = {}, Us = {};
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.regexpCode = e.getEsmExportName = e.getProperty = e.safeStringify = e.stringify = e.strConcat = e.addCodeArg = e.str = e._ = e.nil = e._Code = e.Name = e.IDENTIFIER = e._CodeOrName = void 0;
  class t {
  }
  e._CodeOrName = t, e.IDENTIFIER = /^[a-z$_][a-z$_0-9]*$/i;
  class i extends t {
    constructor(k) {
      if (super(), !e.IDENTIFIER.test(k))
        throw new Error("CodeGen: name must be a valid identifier");
      this.str = k;
    }
    toString() {
      return this.str;
    }
    emptyStr() {
      return !1;
    }
    get names() {
      return { [this.str]: 1 };
    }
  }
  e.Name = i;
  class o extends t {
    constructor(k) {
      super(), this._items = typeof k == "string" ? [k] : k;
    }
    toString() {
      return this.str;
    }
    emptyStr() {
      if (this._items.length > 1)
        return !1;
      const k = this._items[0];
      return k === "" || k === '""';
    }
    get str() {
      var k;
      return (k = this._str) !== null && k !== void 0 ? k : this._str = this._items.reduce((j, T) => `${j}${T}`, "");
    }
    get names() {
      var k;
      return (k = this._names) !== null && k !== void 0 ? k : this._names = this._items.reduce((j, T) => (T instanceof i && (j[T.str] = (j[T.str] || 0) + 1), j), {});
    }
  }
  e._Code = o, e.nil = new o("");
  function a(E, ...k) {
    const j = [E[0]];
    let T = 0;
    for (; T < k.length; )
      f(j, k[T]), j.push(E[++T]);
    return new o(j);
  }
  e._ = a;
  const l = new o("+");
  function c(E, ...k) {
    const j = [$(E[0])];
    let T = 0;
    for (; T < k.length; )
      j.push(l), f(j, k[T]), j.push(l, $(E[++T]));
    return d(j), new o(j);
  }
  e.str = c;
  function f(E, k) {
    k instanceof o ? E.push(...k._items) : k instanceof i ? E.push(k) : E.push(h(k));
  }
  e.addCodeArg = f;
  function d(E) {
    let k = 1;
    for (; k < E.length - 1; ) {
      if (E[k] === l) {
        const j = m(E[k - 1], E[k + 1]);
        if (j !== void 0) {
          E.splice(k - 1, 3, j);
          continue;
        }
        E[k++] = "+";
      }
      k++;
    }
  }
  function m(E, k) {
    if (k === '""')
      return E;
    if (E === '""')
      return k;
    if (typeof E == "string")
      return k instanceof i || E[E.length - 1] !== '"' ? void 0 : typeof k != "string" ? `${E.slice(0, -1)}${k}"` : k[0] === '"' ? E.slice(0, -1) + k.slice(1) : void 0;
    if (typeof k == "string" && k[0] === '"' && !(E instanceof i))
      return `"${E}${k.slice(1)}`;
  }
  function y(E, k) {
    return k.emptyStr() ? E : E.emptyStr() ? k : c`${E}${k}`;
  }
  e.strConcat = y;
  function h(E) {
    return typeof E == "number" || typeof E == "boolean" || E === null ? E : $(Array.isArray(E) ? E.join(",") : E);
  }
  function S(E) {
    return new o($(E));
  }
  e.stringify = S;
  function $(E) {
    return JSON.stringify(E).replace(/\u2028/g, "\\u2028").replace(/\u2029/g, "\\u2029");
  }
  e.safeStringify = $;
  function v(E) {
    return typeof E == "string" && e.IDENTIFIER.test(E) ? new o(`.${E}`) : a`[${E}]`;
  }
  e.getProperty = v;
  function w(E) {
    if (typeof E == "string" && e.IDENTIFIER.test(E))
      return new o(`${E}`);
    throw new Error(`CodeGen: invalid export name: ${E}, use explicit $id name mapping`);
  }
  e.getEsmExportName = w;
  function _(E) {
    return new o(E.toString());
  }
  e.regexpCode = _;
})(Us);
var Bf = {};
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.ValueScope = e.ValueScopeName = e.Scope = e.varKinds = e.UsedValueState = void 0;
  const t = Us;
  class i extends Error {
    constructor(m) {
      super(`CodeGen: "code" for ${m} not defined`), this.value = m.value;
    }
  }
  var o;
  (function(d) {
    d[d.Started = 0] = "Started", d[d.Completed = 1] = "Completed";
  })(o || (e.UsedValueState = o = {})), e.varKinds = {
    const: new t.Name("const"),
    let: new t.Name("let"),
    var: new t.Name("var")
  };
  class a {
    constructor({ prefixes: m, parent: y } = {}) {
      this._names = {}, this._prefixes = m, this._parent = y;
    }
    toName(m) {
      return m instanceof t.Name ? m : this.name(m);
    }
    name(m) {
      return new t.Name(this._newName(m));
    }
    _newName(m) {
      const y = this._names[m] || this._nameGroup(m);
      return `${m}${y.index++}`;
    }
    _nameGroup(m) {
      var y, h;
      if (!((h = (y = this._parent) === null || y === void 0 ? void 0 : y._prefixes) === null || h === void 0) && h.has(m) || this._prefixes && !this._prefixes.has(m))
        throw new Error(`CodeGen: prefix "${m}" is not allowed in this scope`);
      return this._names[m] = { prefix: m, index: 0 };
    }
  }
  e.Scope = a;
  class l extends t.Name {
    constructor(m, y) {
      super(y), this.prefix = m;
    }
    setValue(m, { property: y, itemIndex: h }) {
      this.value = m, this.scopePath = (0, t._)`.${new t.Name(y)}[${h}]`;
    }
  }
  e.ValueScopeName = l;
  const c = (0, t._)`\n`;
  class f extends a {
    constructor(m) {
      super(m), this._values = {}, this._scope = m.scope, this.opts = { ...m, _n: m.lines ? c : t.nil };
    }
    get() {
      return this._scope;
    }
    name(m) {
      return new l(m, this._newName(m));
    }
    value(m, y) {
      var h;
      if (y.ref === void 0)
        throw new Error("CodeGen: ref must be passed in value");
      const S = this.toName(m), { prefix: $ } = S, v = (h = y.key) !== null && h !== void 0 ? h : y.ref;
      let w = this._values[$];
      if (w) {
        const k = w.get(v);
        if (k)
          return k;
      } else
        w = this._values[$] = /* @__PURE__ */ new Map();
      w.set(v, S);
      const _ = this._scope[$] || (this._scope[$] = []), E = _.length;
      return _[E] = y.ref, S.setValue(y, { property: $, itemIndex: E }), S;
    }
    getValue(m, y) {
      const h = this._values[m];
      if (h)
        return h.get(y);
    }
    scopeRefs(m, y = this._values) {
      return this._reduceValues(y, (h) => {
        if (h.scopePath === void 0)
          throw new Error(`CodeGen: name "${h}" has no value`);
        return (0, t._)`${m}${h.scopePath}`;
      });
    }
    scopeCode(m = this._values, y, h) {
      return this._reduceValues(m, (S) => {
        if (S.value === void 0)
          throw new Error(`CodeGen: name "${S}" has no value`);
        return S.value.code;
      }, y, h);
    }
    _reduceValues(m, y, h = {}, S) {
      let $ = t.nil;
      for (const v in m) {
        const w = m[v];
        if (!w)
          continue;
        const _ = h[v] = h[v] || /* @__PURE__ */ new Map();
        w.forEach((E) => {
          if (_.has(E))
            return;
          _.set(E, o.Started);
          let k = y(E);
          if (k) {
            const j = this.opts.es5 ? e.varKinds.var : e.varKinds.const;
            $ = (0, t._)`${$}${j} ${E} = ${k};${this.opts._n}`;
          } else if (k = S == null ? void 0 : S(E))
            $ = (0, t._)`${$}${k}${this.opts._n}`;
          else
            throw new i(E);
          _.set(E, o.Completed);
        });
      }
      return $;
    }
  }
  e.ValueScope = f;
})(Bf);
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.or = e.and = e.not = e.CodeGen = e.operators = e.varKinds = e.ValueScopeName = e.ValueScope = e.Scope = e.Name = e.regexpCode = e.stringify = e.getProperty = e.nil = e.strConcat = e.str = e._ = void 0;
  const t = Us, i = Bf;
  var o = Us;
  Object.defineProperty(e, "_", { enumerable: !0, get: function() {
    return o._;
  } }), Object.defineProperty(e, "str", { enumerable: !0, get: function() {
    return o.str;
  } }), Object.defineProperty(e, "strConcat", { enumerable: !0, get: function() {
    return o.strConcat;
  } }), Object.defineProperty(e, "nil", { enumerable: !0, get: function() {
    return o.nil;
  } }), Object.defineProperty(e, "getProperty", { enumerable: !0, get: function() {
    return o.getProperty;
  } }), Object.defineProperty(e, "stringify", { enumerable: !0, get: function() {
    return o.stringify;
  } }), Object.defineProperty(e, "regexpCode", { enumerable: !0, get: function() {
    return o.regexpCode;
  } }), Object.defineProperty(e, "Name", { enumerable: !0, get: function() {
    return o.Name;
  } });
  var a = Bf;
  Object.defineProperty(e, "Scope", { enumerable: !0, get: function() {
    return a.Scope;
  } }), Object.defineProperty(e, "ValueScope", { enumerable: !0, get: function() {
    return a.ValueScope;
  } }), Object.defineProperty(e, "ValueScopeName", { enumerable: !0, get: function() {
    return a.ValueScopeName;
  } }), Object.defineProperty(e, "varKinds", { enumerable: !0, get: function() {
    return a.varKinds;
  } }), e.operators = {
    GT: new t._Code(">"),
    GTE: new t._Code(">="),
    LT: new t._Code("<"),
    LTE: new t._Code("<="),
    EQ: new t._Code("==="),
    NEQ: new t._Code("!=="),
    NOT: new t._Code("!"),
    OR: new t._Code("||"),
    AND: new t._Code("&&"),
    ADD: new t._Code("+")
  };
  class l {
    optimizeNodes() {
      return this;
    }
    optimizeNames(C, I) {
      return this;
    }
  }
  class c extends l {
    constructor(C, I, B) {
      super(), this.varKind = C, this.name = I, this.rhs = B;
    }
    render({ es5: C, _n: I }) {
      const B = C ? i.varKinds.var : this.varKind, X = this.rhs === void 0 ? "" : ` = ${this.rhs}`;
      return `${B} ${this.name}${X};` + I;
    }
    optimizeNames(C, I) {
      if (C[this.name.str])
        return this.rhs && (this.rhs = le(this.rhs, C, I)), this;
    }
    get names() {
      return this.rhs instanceof t._CodeOrName ? this.rhs.names : {};
    }
  }
  class f extends l {
    constructor(C, I, B) {
      super(), this.lhs = C, this.rhs = I, this.sideEffects = B;
    }
    render({ _n: C }) {
      return `${this.lhs} = ${this.rhs};` + C;
    }
    optimizeNames(C, I) {
      if (!(this.lhs instanceof t.Name && !C[this.lhs.str] && !this.sideEffects))
        return this.rhs = le(this.rhs, C, I), this;
    }
    get names() {
      const C = this.lhs instanceof t.Name ? {} : { ...this.lhs.names };
      return q(C, this.rhs);
    }
  }
  class d extends f {
    constructor(C, I, B, X) {
      super(C, B, X), this.op = I;
    }
    render({ _n: C }) {
      return `${this.lhs} ${this.op}= ${this.rhs};` + C;
    }
  }
  class m extends l {
    constructor(C) {
      super(), this.label = C, this.names = {};
    }
    render({ _n: C }) {
      return `${this.label}:` + C;
    }
  }
  class y extends l {
    constructor(C) {
      super(), this.label = C, this.names = {};
    }
    render({ _n: C }) {
      return `break${this.label ? ` ${this.label}` : ""};` + C;
    }
  }
  class h extends l {
    constructor(C) {
      super(), this.error = C;
    }
    render({ _n: C }) {
      return `throw ${this.error};` + C;
    }
    get names() {
      return this.error.names;
    }
  }
  class S extends l {
    constructor(C) {
      super(), this.code = C;
    }
    render({ _n: C }) {
      return `${this.code};` + C;
    }
    optimizeNodes() {
      return `${this.code}` ? this : void 0;
    }
    optimizeNames(C, I) {
      return this.code = le(this.code, C, I), this;
    }
    get names() {
      return this.code instanceof t._CodeOrName ? this.code.names : {};
    }
  }
  class $ extends l {
    constructor(C = []) {
      super(), this.nodes = C;
    }
    render(C) {
      return this.nodes.reduce((I, B) => I + B.render(C), "");
    }
    optimizeNodes() {
      const { nodes: C } = this;
      let I = C.length;
      for (; I--; ) {
        const B = C[I].optimizeNodes();
        Array.isArray(B) ? C.splice(I, 1, ...B) : B ? C[I] = B : C.splice(I, 1);
      }
      return C.length > 0 ? this : void 0;
    }
    optimizeNames(C, I) {
      const { nodes: B } = this;
      let X = B.length;
      for (; X--; ) {
        const J = B[X];
        J.optimizeNames(C, I) || (ie(C, J.names), B.splice(X, 1));
      }
      return B.length > 0 ? this : void 0;
    }
    get names() {
      return this.nodes.reduce((C, I) => H(C, I.names), {});
    }
  }
  class v extends $ {
    render(C) {
      return "{" + C._n + super.render(C) + "}" + C._n;
    }
  }
  class w extends $ {
  }
  class _ extends v {
  }
  _.kind = "else";
  class E extends v {
    constructor(C, I) {
      super(I), this.condition = C;
    }
    render(C) {
      let I = `if(${this.condition})` + super.render(C);
      return this.else && (I += "else " + this.else.render(C)), I;
    }
    optimizeNodes() {
      super.optimizeNodes();
      const C = this.condition;
      if (C === !0)
        return this.nodes;
      let I = this.else;
      if (I) {
        const B = I.optimizeNodes();
        I = this.else = Array.isArray(B) ? new _(B) : B;
      }
      if (I)
        return C === !1 ? I instanceof E ? I : I.nodes : this.nodes.length ? this : new E(ne(C), I instanceof E ? [I] : I.nodes);
      if (!(C === !1 || !this.nodes.length))
        return this;
    }
    optimizeNames(C, I) {
      var B;
      if (this.else = (B = this.else) === null || B === void 0 ? void 0 : B.optimizeNames(C, I), !!(super.optimizeNames(C, I) || this.else))
        return this.condition = le(this.condition, C, I), this;
    }
    get names() {
      const C = super.names;
      return q(C, this.condition), this.else && H(C, this.else.names), C;
    }
  }
  E.kind = "if";
  class k extends v {
  }
  k.kind = "for";
  class j extends k {
    constructor(C) {
      super(), this.iteration = C;
    }
    render(C) {
      return `for(${this.iteration})` + super.render(C);
    }
    optimizeNames(C, I) {
      if (super.optimizeNames(C, I))
        return this.iteration = le(this.iteration, C, I), this;
    }
    get names() {
      return H(super.names, this.iteration.names);
    }
  }
  class T extends k {
    constructor(C, I, B, X) {
      super(), this.varKind = C, this.name = I, this.from = B, this.to = X;
    }
    render(C) {
      const I = C.es5 ? i.varKinds.var : this.varKind, { name: B, from: X, to: J } = this;
      return `for(${I} ${B}=${X}; ${B}<${J}; ${B}++)` + super.render(C);
    }
    get names() {
      const C = q(super.names, this.from);
      return q(C, this.to);
    }
  }
  class N extends k {
    constructor(C, I, B, X) {
      super(), this.loop = C, this.varKind = I, this.name = B, this.iterable = X;
    }
    render(C) {
      return `for(${this.varKind} ${this.name} ${this.loop} ${this.iterable})` + super.render(C);
    }
    optimizeNames(C, I) {
      if (super.optimizeNames(C, I))
        return this.iterable = le(this.iterable, C, I), this;
    }
    get names() {
      return H(super.names, this.iterable.names);
    }
  }
  class x extends v {
    constructor(C, I, B) {
      super(), this.name = C, this.args = I, this.async = B;
    }
    render(C) {
      return `${this.async ? "async " : ""}function ${this.name}(${this.args})` + super.render(C);
    }
  }
  x.kind = "func";
  class F extends $ {
    render(C) {
      return "return " + super.render(C);
    }
  }
  F.kind = "return";
  class V extends v {
    render(C) {
      let I = "try" + super.render(C);
      return this.catch && (I += this.catch.render(C)), this.finally && (I += this.finally.render(C)), I;
    }
    optimizeNodes() {
      var C, I;
      return super.optimizeNodes(), (C = this.catch) === null || C === void 0 || C.optimizeNodes(), (I = this.finally) === null || I === void 0 || I.optimizeNodes(), this;
    }
    optimizeNames(C, I) {
      var B, X;
      return super.optimizeNames(C, I), (B = this.catch) === null || B === void 0 || B.optimizeNames(C, I), (X = this.finally) === null || X === void 0 || X.optimizeNames(C, I), this;
    }
    get names() {
      const C = super.names;
      return this.catch && H(C, this.catch.names), this.finally && H(C, this.finally.names), C;
    }
  }
  class U extends v {
    constructor(C) {
      super(), this.error = C;
    }
    render(C) {
      return `catch(${this.error})` + super.render(C);
    }
  }
  U.kind = "catch";
  class G extends v {
    render(C) {
      return "finally" + super.render(C);
    }
  }
  G.kind = "finally";
  class Q {
    constructor(C, I = {}) {
      this._values = {}, this._blockStarts = [], this._constants = {}, this.opts = { ...I, _n: I.lines ? `
` : "" }, this._extScope = C, this._scope = new i.Scope({ parent: C }), this._nodes = [new w()];
    }
    toString() {
      return this._root.render(this.opts);
    }
    // returns unique name in the internal scope
    name(C) {
      return this._scope.name(C);
    }
    // reserves unique name in the external scope
    scopeName(C) {
      return this._extScope.name(C);
    }
    // reserves unique name in the external scope and assigns value to it
    scopeValue(C, I) {
      const B = this._extScope.value(C, I);
      return (this._values[B.prefix] || (this._values[B.prefix] = /* @__PURE__ */ new Set())).add(B), B;
    }
    getScopeValue(C, I) {
      return this._extScope.getValue(C, I);
    }
    // return code that assigns values in the external scope to the names that are used internally
    // (same names that were returned by gen.scopeName or gen.scopeValue)
    scopeRefs(C) {
      return this._extScope.scopeRefs(C, this._values);
    }
    scopeCode() {
      return this._extScope.scopeCode(this._values);
    }
    _def(C, I, B, X) {
      const J = this._scope.toName(I);
      return B !== void 0 && X && (this._constants[J.str] = B), this._leafNode(new c(C, J, B)), J;
    }
    // `const` declaration (`var` in es5 mode)
    const(C, I, B) {
      return this._def(i.varKinds.const, C, I, B);
    }
    // `let` declaration with optional assignment (`var` in es5 mode)
    let(C, I, B) {
      return this._def(i.varKinds.let, C, I, B);
    }
    // `var` declaration with optional assignment
    var(C, I, B) {
      return this._def(i.varKinds.var, C, I, B);
    }
    // assignment code
    assign(C, I, B) {
      return this._leafNode(new f(C, I, B));
    }
    // `+=` code
    add(C, I) {
      return this._leafNode(new d(C, e.operators.ADD, I));
    }
    // appends passed SafeExpr to code or executes Block
    code(C) {
      return typeof C == "function" ? C() : C !== t.nil && this._leafNode(new S(C)), this;
    }
    // returns code for object literal for the passed argument list of key-value pairs
    object(...C) {
      const I = ["{"];
      for (const [B, X] of C)
        I.length > 1 && I.push(","), I.push(B), (B !== X || this.opts.es5) && (I.push(":"), (0, t.addCodeArg)(I, X));
      return I.push("}"), new t._Code(I);
    }
    // `if` clause (or statement if `thenBody` and, optionally, `elseBody` are passed)
    if(C, I, B) {
      if (this._blockNode(new E(C)), I && B)
        this.code(I).else().code(B).endIf();
      else if (I)
        this.code(I).endIf();
      else if (B)
        throw new Error('CodeGen: "else" body without "then" body');
      return this;
    }
    // `else if` clause - invalid without `if` or after `else` clauses
    elseIf(C) {
      return this._elseNode(new E(C));
    }
    // `else` clause - only valid after `if` or `else if` clauses
    else() {
      return this._elseNode(new _());
    }
    // end `if` statement (needed if gen.if was used only with condition)
    endIf() {
      return this._endBlockNode(E, _);
    }
    _for(C, I) {
      return this._blockNode(C), I && this.code(I).endFor(), this;
    }
    // a generic `for` clause (or statement if `forBody` is passed)
    for(C, I) {
      return this._for(new j(C), I);
    }
    // `for` statement for a range of values
    forRange(C, I, B, X, J = this.opts.es5 ? i.varKinds.var : i.varKinds.let) {
      const se = this._scope.toName(C);
      return this._for(new T(J, se, I, B), () => X(se));
    }
    // `for-of` statement (in es5 mode replace with a normal for loop)
    forOf(C, I, B, X = i.varKinds.const) {
      const J = this._scope.toName(C);
      if (this.opts.es5) {
        const se = I instanceof t.Name ? I : this.var("_arr", I);
        return this.forRange("_i", 0, (0, t._)`${se}.length`, (ce) => {
          this.var(J, (0, t._)`${se}[${ce}]`), B(J);
        });
      }
      return this._for(new N("of", X, J, I), () => B(J));
    }
    // `for-in` statement.
    // With option `ownProperties` replaced with a `for-of` loop for object keys
    forIn(C, I, B, X = this.opts.es5 ? i.varKinds.var : i.varKinds.const) {
      if (this.opts.ownProperties)
        return this.forOf(C, (0, t._)`Object.keys(${I})`, B);
      const J = this._scope.toName(C);
      return this._for(new N("in", X, J, I), () => B(J));
    }
    // end `for` loop
    endFor() {
      return this._endBlockNode(k);
    }
    // `label` statement
    label(C) {
      return this._leafNode(new m(C));
    }
    // `break` statement
    break(C) {
      return this._leafNode(new y(C));
    }
    // `return` statement
    return(C) {
      const I = new F();
      if (this._blockNode(I), this.code(C), I.nodes.length !== 1)
        throw new Error('CodeGen: "return" should have one node');
      return this._endBlockNode(F);
    }
    // `try` statement
    try(C, I, B) {
      if (!I && !B)
        throw new Error('CodeGen: "try" without "catch" and "finally"');
      const X = new V();
      if (this._blockNode(X), this.code(C), I) {
        const J = this.name("e");
        this._currNode = X.catch = new U(J), I(J);
      }
      return B && (this._currNode = X.finally = new G(), this.code(B)), this._endBlockNode(U, G);
    }
    // `throw` statement
    throw(C) {
      return this._leafNode(new h(C));
    }
    // start self-balancing block
    block(C, I) {
      return this._blockStarts.push(this._nodes.length), C && this.code(C).endBlock(I), this;
    }
    // end the current self-balancing block
    endBlock(C) {
      const I = this._blockStarts.pop();
      if (I === void 0)
        throw new Error("CodeGen: not in self-balancing block");
      const B = this._nodes.length - I;
      if (B < 0 || C !== void 0 && B !== C)
        throw new Error(`CodeGen: wrong number of nodes: ${B} vs ${C} expected`);
      return this._nodes.length = I, this;
    }
    // `function` heading (or definition if funcBody is passed)
    func(C, I = t.nil, B, X) {
      return this._blockNode(new x(C, I, B)), X && this.code(X).endFunc(), this;
    }
    // end function definition
    endFunc() {
      return this._endBlockNode(x);
    }
    optimize(C = 1) {
      for (; C-- > 0; )
        this._root.optimizeNodes(), this._root.optimizeNames(this._root.names, this._constants);
    }
    _leafNode(C) {
      return this._currNode.nodes.push(C), this;
    }
    _blockNode(C) {
      this._currNode.nodes.push(C), this._nodes.push(C);
    }
    _endBlockNode(C, I) {
      const B = this._currNode;
      if (B instanceof C || I && B instanceof I)
        return this._nodes.pop(), this;
      throw new Error(`CodeGen: not in block "${I ? `${C.kind}/${I.kind}` : C.kind}"`);
    }
    _elseNode(C) {
      const I = this._currNode;
      if (!(I instanceof E))
        throw new Error('CodeGen: "else" without "if"');
      return this._currNode = I.else = C, this;
    }
    get _root() {
      return this._nodes[0];
    }
    get _currNode() {
      const C = this._nodes;
      return C[C.length - 1];
    }
    set _currNode(C) {
      const I = this._nodes;
      I[I.length - 1] = C;
    }
  }
  e.CodeGen = Q;
  function H(R, C) {
    for (const I in C)
      R[I] = (R[I] || 0) + (C[I] || 0);
    return R;
  }
  function q(R, C) {
    return C instanceof t._CodeOrName ? H(R, C.names) : R;
  }
  function le(R, C, I) {
    if (R instanceof t.Name)
      return B(R);
    if (!X(R))
      return R;
    return new t._Code(R._items.reduce((J, se) => (se instanceof t.Name && (se = B(se)), se instanceof t._Code ? J.push(...se._items) : J.push(se), J), []));
    function B(J) {
      const se = I[J.str];
      return se === void 0 || C[J.str] !== 1 ? J : (delete C[J.str], se);
    }
    function X(J) {
      return J instanceof t._Code && J._items.some((se) => se instanceof t.Name && C[se.str] === 1 && I[se.str] !== void 0);
    }
  }
  function ie(R, C) {
    for (const I in C)
      R[I] = (R[I] || 0) - (C[I] || 0);
  }
  function ne(R) {
    return typeof R == "boolean" || typeof R == "number" || R === null ? !R : (0, t._)`!${b(R)}`;
  }
  e.not = ne;
  const pe = P(e.operators.AND);
  function Z(...R) {
    return R.reduce(pe);
  }
  e.and = Z;
  const ae = P(e.operators.OR);
  function z(...R) {
    return R.reduce(ae);
  }
  e.or = z;
  function P(R) {
    return (C, I) => C === t.nil ? I : I === t.nil ? C : (0, t._)`${b(C)} ${R} ${b(I)}`;
  }
  function b(R) {
    return R instanceof t.Name ? R : (0, t._)`(${R})`;
  }
})(Te);
var he = {};
Object.defineProperty(he, "__esModule", { value: !0 });
he.checkStrictMode = he.getErrorPath = he.Type = he.useFunc = he.setEvaluated = he.evaluatedPropsToName = he.mergeEvaluated = he.eachItem = he.unescapeJsonPointer = he.escapeJsonPointer = he.escapeFragment = he.unescapeFragment = he.schemaRefOrVal = he.schemaHasRulesButRef = he.schemaHasRules = he.checkUnknownRules = he.alwaysValidSchema = he.toHash = void 0;
const We = Te, rA = Us;
function iA(e) {
  const t = {};
  for (const i of e)
    t[i] = !0;
  return t;
}
he.toHash = iA;
function oA(e, t) {
  return typeof t == "boolean" ? t : Object.keys(t).length === 0 ? !0 : (w_(e, t), !E_(t, e.self.RULES.all));
}
he.alwaysValidSchema = oA;
function w_(e, t = e.schema) {
  const { opts: i, self: o } = e;
  if (!i.strictSchema || typeof t == "boolean")
    return;
  const a = o.RULES.keywords;
  for (const l in t)
    a[l] || P_(e, `unknown keyword: "${l}"`);
}
he.checkUnknownRules = w_;
function E_(e, t) {
  if (typeof e == "boolean")
    return !e;
  for (const i in e)
    if (t[i])
      return !0;
  return !1;
}
he.schemaHasRules = E_;
function sA(e, t) {
  if (typeof e == "boolean")
    return !e;
  for (const i in e)
    if (i !== "$ref" && t.all[i])
      return !0;
  return !1;
}
he.schemaHasRulesButRef = sA;
function aA({ topSchemaRef: e, schemaPath: t }, i, o, a) {
  if (!a) {
    if (typeof i == "number" || typeof i == "boolean")
      return i;
    if (typeof i == "string")
      return (0, We._)`${i}`;
  }
  return (0, We._)`${e}${t}${(0, We.getProperty)(o)}`;
}
he.schemaRefOrVal = aA;
function lA(e) {
  return $_(decodeURIComponent(e));
}
he.unescapeFragment = lA;
function uA(e) {
  return encodeURIComponent(Dd(e));
}
he.escapeFragment = uA;
function Dd(e) {
  return typeof e == "number" ? `${e}` : e.replace(/~/g, "~0").replace(/\//g, "~1");
}
he.escapeJsonPointer = Dd;
function $_(e) {
  return e.replace(/~1/g, "/").replace(/~0/g, "~");
}
he.unescapeJsonPointer = $_;
function cA(e, t) {
  if (Array.isArray(e))
    for (const i of e)
      t(i);
  else
    t(e);
}
he.eachItem = cA;
function zg({ mergeNames: e, mergeToName: t, mergeValues: i, resultToName: o }) {
  return (a, l, c, f) => {
    const d = c === void 0 ? l : c instanceof We.Name ? (l instanceof We.Name ? e(a, l, c) : t(a, l, c), c) : l instanceof We.Name ? (t(a, c, l), l) : i(l, c);
    return f === We.Name && !(d instanceof We.Name) ? o(a, d) : d;
  };
}
he.mergeEvaluated = {
  props: zg({
    mergeNames: (e, t, i) => e.if((0, We._)`${i} !== true && ${t} !== undefined`, () => {
      e.if((0, We._)`${t} === true`, () => e.assign(i, !0), () => e.assign(i, (0, We._)`${i} || {}`).code((0, We._)`Object.assign(${i}, ${t})`));
    }),
    mergeToName: (e, t, i) => e.if((0, We._)`${i} !== true`, () => {
      t === !0 ? e.assign(i, !0) : (e.assign(i, (0, We._)`${i} || {}`), Md(e, i, t));
    }),
    mergeValues: (e, t) => e === !0 ? !0 : { ...e, ...t },
    resultToName: O_
  }),
  items: zg({
    mergeNames: (e, t, i) => e.if((0, We._)`${i} !== true && ${t} !== undefined`, () => e.assign(i, (0, We._)`${t} === true ? true : ${i} > ${t} ? ${i} : ${t}`)),
    mergeToName: (e, t, i) => e.if((0, We._)`${i} !== true`, () => e.assign(i, t === !0 ? !0 : (0, We._)`${i} > ${t} ? ${i} : ${t}`)),
    mergeValues: (e, t) => e === !0 ? !0 : Math.max(e, t),
    resultToName: (e, t) => e.var("items", t)
  })
};
function O_(e, t) {
  if (t === !0)
    return e.var("props", !0);
  const i = e.var("props", (0, We._)`{}`);
  return t !== void 0 && Md(e, i, t), i;
}
he.evaluatedPropsToName = O_;
function Md(e, t, i) {
  Object.keys(i).forEach((o) => e.assign((0, We._)`${t}${(0, We.getProperty)(o)}`, !0));
}
he.setEvaluated = Md;
const Vg = {};
function fA(e, t) {
  return e.scopeValue("func", {
    ref: t,
    code: Vg[t.code] || (Vg[t.code] = new rA._Code(t.code))
  });
}
he.useFunc = fA;
var Kf;
(function(e) {
  e[e.Num = 0] = "Num", e[e.Str = 1] = "Str";
})(Kf || (he.Type = Kf = {}));
function dA(e, t, i) {
  if (e instanceof We.Name) {
    const o = t === Kf.Num;
    return i ? o ? (0, We._)`"[" + ${e} + "]"` : (0, We._)`"['" + ${e} + "']"` : o ? (0, We._)`"/" + ${e}` : (0, We._)`"/" + ${e}.replace(/~/g, "~0").replace(/\\//g, "~1")`;
  }
  return i ? (0, We.getProperty)(e).toString() : "/" + Dd(e);
}
he.getErrorPath = dA;
function P_(e, t, i = e.opts.strictSchema) {
  if (i) {
    if (t = `strict mode: ${t}`, i === !0)
      throw new Error(t);
    e.self.logger.warn(t);
  }
}
he.checkStrictMode = P_;
var Kn = {};
Object.defineProperty(Kn, "__esModule", { value: !0 });
const It = Te, pA = {
  // validation function arguments
  data: new It.Name("data"),
  // data passed to validation function
  // args passed from referencing schema
  valCxt: new It.Name("valCxt"),
  // validation/data context - should not be used directly, it is destructured to the names below
  instancePath: new It.Name("instancePath"),
  parentData: new It.Name("parentData"),
  parentDataProperty: new It.Name("parentDataProperty"),
  rootData: new It.Name("rootData"),
  // root data - same as the data passed to the first/top validation function
  dynamicAnchors: new It.Name("dynamicAnchors"),
  // used to support recursiveRef and dynamicRef
  // function scoped variables
  vErrors: new It.Name("vErrors"),
  // null or array of validation errors
  errors: new It.Name("errors"),
  // counter of validation errors
  this: new It.Name("this"),
  // "globals"
  self: new It.Name("self"),
  scope: new It.Name("scope"),
  // JTD serialize/parse name for JSON string and position
  json: new It.Name("json"),
  jsonPos: new It.Name("jsonPos"),
  jsonLen: new It.Name("jsonLen"),
  jsonPart: new It.Name("jsonPart")
};
Kn.default = pA;
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.extendErrors = e.resetErrorsCount = e.reportExtraError = e.reportError = e.keyword$DataError = e.keywordError = void 0;
  const t = Te, i = he, o = Kn;
  e.keywordError = {
    message: ({ keyword: _ }) => (0, t.str)`must pass "${_}" keyword validation`
  }, e.keyword$DataError = {
    message: ({ keyword: _, schemaType: E }) => E ? (0, t.str)`"${_}" keyword must be ${E} ($data)` : (0, t.str)`"${_}" keyword is invalid ($data)`
  };
  function a(_, E = e.keywordError, k, j) {
    const { it: T } = _, { gen: N, compositeRule: x, allErrors: F } = T, V = h(_, E, k);
    j ?? (x || F) ? d(N, V) : m(T, (0, t._)`[${V}]`);
  }
  e.reportError = a;
  function l(_, E = e.keywordError, k) {
    const { it: j } = _, { gen: T, compositeRule: N, allErrors: x } = j, F = h(_, E, k);
    d(T, F), N || x || m(j, o.default.vErrors);
  }
  e.reportExtraError = l;
  function c(_, E) {
    _.assign(o.default.errors, E), _.if((0, t._)`${o.default.vErrors} !== null`, () => _.if(E, () => _.assign((0, t._)`${o.default.vErrors}.length`, E), () => _.assign(o.default.vErrors, null)));
  }
  e.resetErrorsCount = c;
  function f({ gen: _, keyword: E, schemaValue: k, data: j, errsCount: T, it: N }) {
    if (T === void 0)
      throw new Error("ajv implementation error");
    const x = _.name("err");
    _.forRange("i", T, o.default.errors, (F) => {
      _.const(x, (0, t._)`${o.default.vErrors}[${F}]`), _.if((0, t._)`${x}.instancePath === undefined`, () => _.assign((0, t._)`${x}.instancePath`, (0, t.strConcat)(o.default.instancePath, N.errorPath))), _.assign((0, t._)`${x}.schemaPath`, (0, t.str)`${N.errSchemaPath}/${E}`), N.opts.verbose && (_.assign((0, t._)`${x}.schema`, k), _.assign((0, t._)`${x}.data`, j));
    });
  }
  e.extendErrors = f;
  function d(_, E) {
    const k = _.const("err", E);
    _.if((0, t._)`${o.default.vErrors} === null`, () => _.assign(o.default.vErrors, (0, t._)`[${k}]`), (0, t._)`${o.default.vErrors}.push(${k})`), _.code((0, t._)`${o.default.errors}++`);
  }
  function m(_, E) {
    const { gen: k, validateName: j, schemaEnv: T } = _;
    T.$async ? k.throw((0, t._)`new ${_.ValidationError}(${E})`) : (k.assign((0, t._)`${j}.errors`, E), k.return(!1));
  }
  const y = {
    keyword: new t.Name("keyword"),
    schemaPath: new t.Name("schemaPath"),
    // also used in JTD errors
    params: new t.Name("params"),
    propertyName: new t.Name("propertyName"),
    message: new t.Name("message"),
    schema: new t.Name("schema"),
    parentSchema: new t.Name("parentSchema")
  };
  function h(_, E, k) {
    const { createErrors: j } = _.it;
    return j === !1 ? (0, t._)`{}` : S(_, E, k);
  }
  function S(_, E, k = {}) {
    const { gen: j, it: T } = _, N = [
      $(T, k),
      v(_, k)
    ];
    return w(_, E, N), j.object(...N);
  }
  function $({ errorPath: _ }, { instancePath: E }) {
    const k = E ? (0, t.str)`${_}${(0, i.getErrorPath)(E, i.Type.Str)}` : _;
    return [o.default.instancePath, (0, t.strConcat)(o.default.instancePath, k)];
  }
  function v({ keyword: _, it: { errSchemaPath: E } }, { schemaPath: k, parentSchema: j }) {
    let T = j ? E : (0, t.str)`${E}/${_}`;
    return k && (T = (0, t.str)`${T}${(0, i.getErrorPath)(k, i.Type.Str)}`), [y.schemaPath, T];
  }
  function w(_, { params: E, message: k }, j) {
    const { keyword: T, data: N, schemaValue: x, it: F } = _, { opts: V, propertyName: U, topSchemaRef: G, schemaPath: Q } = F;
    j.push([y.keyword, T], [y.params, typeof E == "function" ? E(_) : E || (0, t._)`{}`]), V.messages && j.push([y.message, typeof k == "function" ? k(_) : k]), V.verbose && j.push([y.schema, x], [y.parentSchema, (0, t._)`${G}${Q}`], [o.default.data, N]), U && j.push([y.propertyName, U]);
  }
})(Xs);
Object.defineProperty(vo, "__esModule", { value: !0 });
vo.boolOrEmptySchema = vo.topBoolOrEmptySchema = void 0;
const hA = Xs, mA = Te, yA = Kn, gA = {
  message: "boolean schema is false"
};
function vA(e) {
  const { gen: t, schema: i, validateName: o } = e;
  i === !1 ? C_(e, !1) : typeof i == "object" && i.$async === !0 ? t.return(yA.default.data) : (t.assign((0, mA._)`${o}.errors`, null), t.return(!0));
}
vo.topBoolOrEmptySchema = vA;
function _A(e, t) {
  const { gen: i, schema: o } = e;
  o === !1 ? (i.var(t, !1), C_(e)) : i.var(t, !0);
}
vo.boolOrEmptySchema = _A;
function C_(e, t) {
  const { gen: i, data: o } = e, a = {
    gen: i,
    keyword: "false schema",
    data: o,
    schema: !1,
    schemaCode: !1,
    schemaValue: !1,
    params: {},
    it: e
  };
  (0, hA.reportError)(a, gA, void 0, t);
}
var mt = {}, vi = {};
Object.defineProperty(vi, "__esModule", { value: !0 });
vi.getRules = vi.isJSONType = void 0;
const SA = ["string", "number", "integer", "boolean", "null", "object", "array"], wA = new Set(SA);
function EA(e) {
  return typeof e == "string" && wA.has(e);
}
vi.isJSONType = EA;
function $A() {
  const e = {
    number: { type: "number", rules: [] },
    string: { type: "string", rules: [] },
    array: { type: "array", rules: [] },
    object: { type: "object", rules: [] }
  };
  return {
    types: { ...e, integer: !0, boolean: !0, null: !0 },
    rules: [{ rules: [] }, e.number, e.string, e.array, e.object],
    post: { rules: [] },
    all: {},
    keywords: {}
  };
}
vi.getRules = $A;
var tr = {};
Object.defineProperty(tr, "__esModule", { value: !0 });
tr.shouldUseRule = tr.shouldUseGroup = tr.schemaHasRulesForType = void 0;
function OA({ schema: e, self: t }, i) {
  const o = t.RULES.types[i];
  return o && o !== !0 && k_(e, o);
}
tr.schemaHasRulesForType = OA;
function k_(e, t) {
  return t.rules.some((i) => T_(e, i));
}
tr.shouldUseGroup = k_;
function T_(e, t) {
  var i;
  return e[t.keyword] !== void 0 || ((i = t.definition.implements) === null || i === void 0 ? void 0 : i.some((o) => e[o] !== void 0));
}
tr.shouldUseRule = T_;
Object.defineProperty(mt, "__esModule", { value: !0 });
mt.reportTypeError = mt.checkDataTypes = mt.checkDataType = mt.coerceAndCheckDataType = mt.getJSONTypes = mt.getSchemaTypes = mt.DataType = void 0;
const PA = vi, CA = tr, kA = Xs, Ce = Te, N_ = he;
var co;
(function(e) {
  e[e.Correct = 0] = "Correct", e[e.Wrong = 1] = "Wrong";
})(co || (mt.DataType = co = {}));
function TA(e) {
  const t = I_(e.type);
  if (t.includes("null")) {
    if (e.nullable === !1)
      throw new Error("type: null contradicts nullable: false");
  } else {
    if (!t.length && e.nullable !== void 0)
      throw new Error('"nullable" cannot be used without "type"');
    e.nullable === !0 && t.push("null");
  }
  return t;
}
mt.getSchemaTypes = TA;
function I_(e) {
  const t = Array.isArray(e) ? e : e ? [e] : [];
  if (t.every(PA.isJSONType))
    return t;
  throw new Error("type must be JSONType or JSONType[]: " + t.join(","));
}
mt.getJSONTypes = I_;
function NA(e, t) {
  const { gen: i, data: o, opts: a } = e, l = IA(t, a.coerceTypes), c = t.length > 0 && !(l.length === 0 && t.length === 1 && (0, CA.schemaHasRulesForType)(e, t[0]));
  if (c) {
    const f = Ld(t, o, a.strictNumbers, co.Wrong);
    i.if(f, () => {
      l.length ? jA(e, t, l) : Ud(e);
    });
  }
  return c;
}
mt.coerceAndCheckDataType = NA;
const j_ = /* @__PURE__ */ new Set(["string", "number", "integer", "boolean", "null"]);
function IA(e, t) {
  return t ? e.filter((i) => j_.has(i) || t === "array" && i === "array") : [];
}
function jA(e, t, i) {
  const { gen: o, data: a, opts: l } = e, c = o.let("dataType", (0, Ce._)`typeof ${a}`), f = o.let("coerced", (0, Ce._)`undefined`);
  l.coerceTypes === "array" && o.if((0, Ce._)`${c} == 'object' && Array.isArray(${a}) && ${a}.length == 1`, () => o.assign(a, (0, Ce._)`${a}[0]`).assign(c, (0, Ce._)`typeof ${a}`).if(Ld(t, a, l.strictNumbers), () => o.assign(f, a))), o.if((0, Ce._)`${f} !== undefined`);
  for (const m of i)
    (j_.has(m) || m === "array" && l.coerceTypes === "array") && d(m);
  o.else(), Ud(e), o.endIf(), o.if((0, Ce._)`${f} !== undefined`, () => {
    o.assign(a, f), AA(e, f);
  });
  function d(m) {
    switch (m) {
      case "string":
        o.elseIf((0, Ce._)`${c} == "number" || ${c} == "boolean"`).assign(f, (0, Ce._)`"" + ${a}`).elseIf((0, Ce._)`${a} === null`).assign(f, (0, Ce._)`""`);
        return;
      case "number":
        o.elseIf((0, Ce._)`${c} == "boolean" || ${a} === null
              || (${c} == "string" && ${a} && ${a} == +${a})`).assign(f, (0, Ce._)`+${a}`);
        return;
      case "integer":
        o.elseIf((0, Ce._)`${c} === "boolean" || ${a} === null
              || (${c} === "string" && ${a} && ${a} == +${a} && !(${a} % 1))`).assign(f, (0, Ce._)`+${a}`);
        return;
      case "boolean":
        o.elseIf((0, Ce._)`${a} === "false" || ${a} === 0 || ${a} === null`).assign(f, !1).elseIf((0, Ce._)`${a} === "true" || ${a} === 1`).assign(f, !0);
        return;
      case "null":
        o.elseIf((0, Ce._)`${a} === "" || ${a} === 0 || ${a} === false`), o.assign(f, null);
        return;
      case "array":
        o.elseIf((0, Ce._)`${c} === "string" || ${c} === "number"
              || ${c} === "boolean" || ${a} === null`).assign(f, (0, Ce._)`[${a}]`);
    }
  }
}
function AA({ gen: e, parentData: t, parentDataProperty: i }, o) {
  e.if((0, Ce._)`${t} !== undefined`, () => e.assign((0, Ce._)`${t}[${i}]`, o));
}
function Wf(e, t, i, o = co.Correct) {
  const a = o === co.Correct ? Ce.operators.EQ : Ce.operators.NEQ;
  let l;
  switch (e) {
    case "null":
      return (0, Ce._)`${t} ${a} null`;
    case "array":
      l = (0, Ce._)`Array.isArray(${t})`;
      break;
    case "object":
      l = (0, Ce._)`${t} && typeof ${t} == "object" && !Array.isArray(${t})`;
      break;
    case "integer":
      l = c((0, Ce._)`!(${t} % 1) && !isNaN(${t})`);
      break;
    case "number":
      l = c();
      break;
    default:
      return (0, Ce._)`typeof ${t} ${a} ${e}`;
  }
  return o === co.Correct ? l : (0, Ce.not)(l);
  function c(f = Ce.nil) {
    return (0, Ce.and)((0, Ce._)`typeof ${t} == "number"`, f, i ? (0, Ce._)`isFinite(${t})` : Ce.nil);
  }
}
mt.checkDataType = Wf;
function Ld(e, t, i, o) {
  if (e.length === 1)
    return Wf(e[0], t, i, o);
  let a;
  const l = (0, N_.toHash)(e);
  if (l.array && l.object) {
    const c = (0, Ce._)`typeof ${t} != "object"`;
    a = l.null ? c : (0, Ce._)`!${t} || ${c}`, delete l.null, delete l.array, delete l.object;
  } else
    a = Ce.nil;
  l.number && delete l.integer;
  for (const c in l)
    a = (0, Ce.and)(a, Wf(c, t, i, o));
  return a;
}
mt.checkDataTypes = Ld;
const xA = {
  message: ({ schema: e }) => `must be ${e}`,
  params: ({ schema: e, schemaValue: t }) => typeof e == "string" ? (0, Ce._)`{type: ${e}}` : (0, Ce._)`{type: ${t}}`
};
function Ud(e) {
  const t = bA(e);
  (0, kA.reportError)(t, xA);
}
mt.reportTypeError = Ud;
function bA(e) {
  const { gen: t, data: i, schema: o } = e, a = (0, N_.schemaRefOrVal)(e, o, "type");
  return {
    gen: t,
    keyword: "type",
    data: i,
    schema: o.type,
    schemaCode: a,
    schemaValue: a,
    parentSchema: o,
    params: {},
    it: e
  };
}
var tu = {};
Object.defineProperty(tu, "__esModule", { value: !0 });
tu.assignDefaults = void 0;
const no = Te, FA = he;
function RA(e, t) {
  const { properties: i, items: o } = e.schema;
  if (t === "object" && i)
    for (const a in i)
      Bg(e, a, i[a].default);
  else t === "array" && Array.isArray(o) && o.forEach((a, l) => Bg(e, l, a.default));
}
tu.assignDefaults = RA;
function Bg(e, t, i) {
  const { gen: o, compositeRule: a, data: l, opts: c } = e;
  if (i === void 0)
    return;
  const f = (0, no._)`${l}${(0, no.getProperty)(t)}`;
  if (a) {
    (0, FA.checkStrictMode)(e, `default is ignored for: ${f}`);
    return;
  }
  let d = (0, no._)`${f} === undefined`;
  c.useDefaults === "empty" && (d = (0, no._)`${d} || ${f} === null || ${f} === ""`), o.if(d, (0, no._)`${f} = ${(0, no.stringify)(i)}`);
}
var Ln = {}, je = {};
Object.defineProperty(je, "__esModule", { value: !0 });
je.validateUnion = je.validateArray = je.usePattern = je.callValidateCode = je.schemaProperties = je.allSchemaProperties = je.noPropertyInData = je.propertyInData = je.isOwnProperty = je.hasPropFunc = je.reportMissingProp = je.checkMissingProp = je.checkReportMissingProp = void 0;
const Xe = Te, zd = he, Nr = Kn, DA = he;
function MA(e, t) {
  const { gen: i, data: o, it: a } = e;
  i.if(Bd(i, o, t, a.opts.ownProperties), () => {
    e.setParams({ missingProperty: (0, Xe._)`${t}` }, !0), e.error();
  });
}
je.checkReportMissingProp = MA;
function LA({ gen: e, data: t, it: { opts: i } }, o, a) {
  return (0, Xe.or)(...o.map((l) => (0, Xe.and)(Bd(e, t, l, i.ownProperties), (0, Xe._)`${a} = ${l}`)));
}
je.checkMissingProp = LA;
function UA(e, t) {
  e.setParams({ missingProperty: t }, !0), e.error();
}
je.reportMissingProp = UA;
function A_(e) {
  return e.scopeValue("func", {
    // eslint-disable-next-line @typescript-eslint/unbound-method
    ref: Object.prototype.hasOwnProperty,
    code: (0, Xe._)`Object.prototype.hasOwnProperty`
  });
}
je.hasPropFunc = A_;
function Vd(e, t, i) {
  return (0, Xe._)`${A_(e)}.call(${t}, ${i})`;
}
je.isOwnProperty = Vd;
function zA(e, t, i, o) {
  const a = (0, Xe._)`${t}${(0, Xe.getProperty)(i)} !== undefined`;
  return o ? (0, Xe._)`${a} && ${Vd(e, t, i)}` : a;
}
je.propertyInData = zA;
function Bd(e, t, i, o) {
  const a = (0, Xe._)`${t}${(0, Xe.getProperty)(i)} === undefined`;
  return o ? (0, Xe.or)(a, (0, Xe.not)(Vd(e, t, i))) : a;
}
je.noPropertyInData = Bd;
function x_(e) {
  return e ? Object.keys(e).filter((t) => t !== "__proto__") : [];
}
je.allSchemaProperties = x_;
function VA(e, t) {
  return x_(t).filter((i) => !(0, zd.alwaysValidSchema)(e, t[i]));
}
je.schemaProperties = VA;
function BA({ schemaCode: e, data: t, it: { gen: i, topSchemaRef: o, schemaPath: a, errorPath: l }, it: c }, f, d, m) {
  const y = m ? (0, Xe._)`${e}, ${t}, ${o}${a}` : t, h = [
    [Nr.default.instancePath, (0, Xe.strConcat)(Nr.default.instancePath, l)],
    [Nr.default.parentData, c.parentData],
    [Nr.default.parentDataProperty, c.parentDataProperty],
    [Nr.default.rootData, Nr.default.rootData]
  ];
  c.opts.dynamicRef && h.push([Nr.default.dynamicAnchors, Nr.default.dynamicAnchors]);
  const S = (0, Xe._)`${y}, ${i.object(...h)}`;
  return d !== Xe.nil ? (0, Xe._)`${f}.call(${d}, ${S})` : (0, Xe._)`${f}(${S})`;
}
je.callValidateCode = BA;
const KA = (0, Xe._)`new RegExp`;
function WA({ gen: e, it: { opts: t } }, i) {
  const o = t.unicodeRegExp ? "u" : "", { regExp: a } = t.code, l = a(i, o);
  return e.scopeValue("pattern", {
    key: l.toString(),
    ref: l,
    code: (0, Xe._)`${a.code === "new RegExp" ? KA : (0, DA.useFunc)(e, a)}(${i}, ${o})`
  });
}
je.usePattern = WA;
function HA(e) {
  const { gen: t, data: i, keyword: o, it: a } = e, l = t.name("valid");
  if (a.allErrors) {
    const f = t.let("valid", !0);
    return c(() => t.assign(f, !1)), f;
  }
  return t.var(l, !0), c(() => t.break()), l;
  function c(f) {
    const d = t.const("len", (0, Xe._)`${i}.length`);
    t.forRange("i", 0, d, (m) => {
      e.subschema({
        keyword: o,
        dataProp: m,
        dataPropType: zd.Type.Num
      }, l), t.if((0, Xe.not)(l), f);
    });
  }
}
je.validateArray = HA;
function qA(e) {
  const { gen: t, schema: i, keyword: o, it: a } = e;
  if (!Array.isArray(i))
    throw new Error("ajv implementation error");
  if (i.some((d) => (0, zd.alwaysValidSchema)(a, d)) && !a.opts.unevaluated)
    return;
  const c = t.let("valid", !1), f = t.name("_valid");
  t.block(() => i.forEach((d, m) => {
    const y = e.subschema({
      keyword: o,
      schemaProp: m,
      compositeRule: !0
    }, f);
    t.assign(c, (0, Xe._)`${c} || ${f}`), e.mergeValidEvaluated(y, f) || t.if((0, Xe.not)(c));
  })), e.result(c, () => e.reset(), () => e.error(!0));
}
je.validateUnion = qA;
Object.defineProperty(Ln, "__esModule", { value: !0 });
Ln.validateKeywordUsage = Ln.validSchemaType = Ln.funcKeywordCode = Ln.macroKeywordCode = void 0;
const Ft = Te, ci = Kn, GA = je, YA = Xs;
function QA(e, t) {
  const { gen: i, keyword: o, schema: a, parentSchema: l, it: c } = e, f = t.macro.call(c.self, a, l, c), d = b_(i, o, f);
  c.opts.validateSchema !== !1 && c.self.validateSchema(f, !0);
  const m = i.name("valid");
  e.subschema({
    schema: f,
    schemaPath: Ft.nil,
    errSchemaPath: `${c.errSchemaPath}/${o}`,
    topSchemaRef: d,
    compositeRule: !0
  }, m), e.pass(m, () => e.error(!0));
}
Ln.macroKeywordCode = QA;
function JA(e, t) {
  var i;
  const { gen: o, keyword: a, schema: l, parentSchema: c, $data: f, it: d } = e;
  ZA(d, t);
  const m = !f && t.compile ? t.compile.call(d.self, l, c, d) : t.validate, y = b_(o, a, m), h = o.let("valid");
  e.block$data(h, S), e.ok((i = t.valid) !== null && i !== void 0 ? i : h);
  function S() {
    if (t.errors === !1)
      w(), t.modifying && Kg(e), _(() => e.error());
    else {
      const E = t.async ? $() : v();
      t.modifying && Kg(e), _(() => XA(e, E));
    }
  }
  function $() {
    const E = o.let("ruleErrs", null);
    return o.try(() => w((0, Ft._)`await `), (k) => o.assign(h, !1).if((0, Ft._)`${k} instanceof ${d.ValidationError}`, () => o.assign(E, (0, Ft._)`${k}.errors`), () => o.throw(k))), E;
  }
  function v() {
    const E = (0, Ft._)`${y}.errors`;
    return o.assign(E, null), w(Ft.nil), E;
  }
  function w(E = t.async ? (0, Ft._)`await ` : Ft.nil) {
    const k = d.opts.passContext ? ci.default.this : ci.default.self, j = !("compile" in t && !f || t.schema === !1);
    o.assign(h, (0, Ft._)`${E}${(0, GA.callValidateCode)(e, y, k, j)}`, t.modifying);
  }
  function _(E) {
    var k;
    o.if((0, Ft.not)((k = t.valid) !== null && k !== void 0 ? k : h), E);
  }
}
Ln.funcKeywordCode = JA;
function Kg(e) {
  const { gen: t, data: i, it: o } = e;
  t.if(o.parentData, () => t.assign(i, (0, Ft._)`${o.parentData}[${o.parentDataProperty}]`));
}
function XA(e, t) {
  const { gen: i } = e;
  i.if((0, Ft._)`Array.isArray(${t})`, () => {
    i.assign(ci.default.vErrors, (0, Ft._)`${ci.default.vErrors} === null ? ${t} : ${ci.default.vErrors}.concat(${t})`).assign(ci.default.errors, (0, Ft._)`${ci.default.vErrors}.length`), (0, YA.extendErrors)(e);
  }, () => e.error());
}
function ZA({ schemaEnv: e }, t) {
  if (t.async && !e.$async)
    throw new Error("async keyword in sync schema");
}
function b_(e, t, i) {
  if (i === void 0)
    throw new Error(`keyword "${t}" failed to compile`);
  return e.scopeValue("keyword", typeof i == "function" ? { ref: i } : { ref: i, code: (0, Ft.stringify)(i) });
}
function ex(e, t, i = !1) {
  return !t.length || t.some((o) => o === "array" ? Array.isArray(e) : o === "object" ? e && typeof e == "object" && !Array.isArray(e) : typeof e == o || i && typeof e > "u");
}
Ln.validSchemaType = ex;
function tx({ schema: e, opts: t, self: i, errSchemaPath: o }, a, l) {
  if (Array.isArray(a.keyword) ? !a.keyword.includes(l) : a.keyword !== l)
    throw new Error("ajv implementation error");
  const c = a.dependencies;
  if (c != null && c.some((f) => !Object.prototype.hasOwnProperty.call(e, f)))
    throw new Error(`parent schema must have dependencies of ${l}: ${c.join(",")}`);
  if (a.validateSchema && !a.validateSchema(e[l])) {
    const d = `keyword "${l}" value is invalid at path "${o}": ` + i.errorsText(a.validateSchema.errors);
    if (t.validateSchema === "log")
      i.logger.error(d);
    else
      throw new Error(d);
  }
}
Ln.validateKeywordUsage = tx;
var Lr = {};
Object.defineProperty(Lr, "__esModule", { value: !0 });
Lr.extendSubschemaMode = Lr.extendSubschemaData = Lr.getSubschema = void 0;
const bn = Te, F_ = he;
function nx(e, { keyword: t, schemaProp: i, schema: o, schemaPath: a, errSchemaPath: l, topSchemaRef: c }) {
  if (t !== void 0 && o !== void 0)
    throw new Error('both "keyword" and "schema" passed, only one allowed');
  if (t !== void 0) {
    const f = e.schema[t];
    return i === void 0 ? {
      schema: f,
      schemaPath: (0, bn._)`${e.schemaPath}${(0, bn.getProperty)(t)}`,
      errSchemaPath: `${e.errSchemaPath}/${t}`
    } : {
      schema: f[i],
      schemaPath: (0, bn._)`${e.schemaPath}${(0, bn.getProperty)(t)}${(0, bn.getProperty)(i)}`,
      errSchemaPath: `${e.errSchemaPath}/${t}/${(0, F_.escapeFragment)(i)}`
    };
  }
  if (o !== void 0) {
    if (a === void 0 || l === void 0 || c === void 0)
      throw new Error('"schemaPath", "errSchemaPath" and "topSchemaRef" are required with "schema"');
    return {
      schema: o,
      schemaPath: a,
      topSchemaRef: c,
      errSchemaPath: l
    };
  }
  throw new Error('either "keyword" or "schema" must be passed');
}
Lr.getSubschema = nx;
function rx(e, t, { dataProp: i, dataPropType: o, data: a, dataTypes: l, propertyName: c }) {
  if (a !== void 0 && i !== void 0)
    throw new Error('both "data" and "dataProp" passed, only one allowed');
  const { gen: f } = t;
  if (i !== void 0) {
    const { errorPath: m, dataPathArr: y, opts: h } = t, S = f.let("data", (0, bn._)`${t.data}${(0, bn.getProperty)(i)}`, !0);
    d(S), e.errorPath = (0, bn.str)`${m}${(0, F_.getErrorPath)(i, o, h.jsPropertySyntax)}`, e.parentDataProperty = (0, bn._)`${i}`, e.dataPathArr = [...y, e.parentDataProperty];
  }
  if (a !== void 0) {
    const m = a instanceof bn.Name ? a : f.let("data", a, !0);
    d(m), c !== void 0 && (e.propertyName = c);
  }
  l && (e.dataTypes = l);
  function d(m) {
    e.data = m, e.dataLevel = t.dataLevel + 1, e.dataTypes = [], t.definedProperties = /* @__PURE__ */ new Set(), e.parentData = t.data, e.dataNames = [...t.dataNames, m];
  }
}
Lr.extendSubschemaData = rx;
function ix(e, { jtdDiscriminator: t, jtdMetadata: i, compositeRule: o, createErrors: a, allErrors: l }) {
  o !== void 0 && (e.compositeRule = o), a !== void 0 && (e.createErrors = a), l !== void 0 && (e.allErrors = l), e.jtdDiscriminator = t, e.jtdMetadata = i;
}
Lr.extendSubschemaMode = ix;
var Ot = {}, R_ = function e(t, i) {
  if (t === i) return !0;
  if (t && i && typeof t == "object" && typeof i == "object") {
    if (t.constructor !== i.constructor) return !1;
    var o, a, l;
    if (Array.isArray(t)) {
      if (o = t.length, o != i.length) return !1;
      for (a = o; a-- !== 0; )
        if (!e(t[a], i[a])) return !1;
      return !0;
    }
    if (t.constructor === RegExp) return t.source === i.source && t.flags === i.flags;
    if (t.valueOf !== Object.prototype.valueOf) return t.valueOf() === i.valueOf();
    if (t.toString !== Object.prototype.toString) return t.toString() === i.toString();
    if (l = Object.keys(t), o = l.length, o !== Object.keys(i).length) return !1;
    for (a = o; a-- !== 0; )
      if (!Object.prototype.hasOwnProperty.call(i, l[a])) return !1;
    for (a = o; a-- !== 0; ) {
      var c = l[a];
      if (!e(t[c], i[c])) return !1;
    }
    return !0;
  }
  return t !== t && i !== i;
}, D_ = { exports: {} }, br = D_.exports = function(e, t, i) {
  typeof t == "function" && (i = t, t = {}), i = t.cb || i;
  var o = typeof i == "function" ? i : i.pre || function() {
  }, a = i.post || function() {
  };
  Cl(t, o, a, e, "", e);
};
br.keywords = {
  additionalItems: !0,
  items: !0,
  contains: !0,
  additionalProperties: !0,
  propertyNames: !0,
  not: !0,
  if: !0,
  then: !0,
  else: !0
};
br.arrayKeywords = {
  items: !0,
  allOf: !0,
  anyOf: !0,
  oneOf: !0
};
br.propsKeywords = {
  $defs: !0,
  definitions: !0,
  properties: !0,
  patternProperties: !0,
  dependencies: !0
};
br.skipKeywords = {
  default: !0,
  enum: !0,
  const: !0,
  required: !0,
  maximum: !0,
  minimum: !0,
  exclusiveMaximum: !0,
  exclusiveMinimum: !0,
  multipleOf: !0,
  maxLength: !0,
  minLength: !0,
  pattern: !0,
  format: !0,
  maxItems: !0,
  minItems: !0,
  uniqueItems: !0,
  maxProperties: !0,
  minProperties: !0
};
function Cl(e, t, i, o, a, l, c, f, d, m) {
  if (o && typeof o == "object" && !Array.isArray(o)) {
    t(o, a, l, c, f, d, m);
    for (var y in o) {
      var h = o[y];
      if (Array.isArray(h)) {
        if (y in br.arrayKeywords)
          for (var S = 0; S < h.length; S++)
            Cl(e, t, i, h[S], a + "/" + y + "/" + S, l, a, y, o, S);
      } else if (y in br.propsKeywords) {
        if (h && typeof h == "object")
          for (var $ in h)
            Cl(e, t, i, h[$], a + "/" + y + "/" + ox($), l, a, y, o, $);
      } else (y in br.keywords || e.allKeys && !(y in br.skipKeywords)) && Cl(e, t, i, h, a + "/" + y, l, a, y, o);
    }
    i(o, a, l, c, f, d, m);
  }
}
function ox(e) {
  return e.replace(/~/g, "~0").replace(/\//g, "~1");
}
var sx = D_.exports;
Object.defineProperty(Ot, "__esModule", { value: !0 });
Ot.getSchemaRefs = Ot.resolveUrl = Ot.normalizeId = Ot._getFullPath = Ot.getFullPath = Ot.inlineRef = void 0;
const ax = he, lx = R_, ux = sx, cx = /* @__PURE__ */ new Set([
  "type",
  "format",
  "pattern",
  "maxLength",
  "minLength",
  "maxProperties",
  "minProperties",
  "maxItems",
  "minItems",
  "maximum",
  "minimum",
  "uniqueItems",
  "multipleOf",
  "required",
  "enum",
  "const"
]);
function fx(e, t = !0) {
  return typeof e == "boolean" ? !0 : t === !0 ? !Hf(e) : t ? M_(e) <= t : !1;
}
Ot.inlineRef = fx;
const dx = /* @__PURE__ */ new Set([
  "$ref",
  "$recursiveRef",
  "$recursiveAnchor",
  "$dynamicRef",
  "$dynamicAnchor"
]);
function Hf(e) {
  for (const t in e) {
    if (dx.has(t))
      return !0;
    const i = e[t];
    if (Array.isArray(i) && i.some(Hf) || typeof i == "object" && Hf(i))
      return !0;
  }
  return !1;
}
function M_(e) {
  let t = 0;
  for (const i in e) {
    if (i === "$ref")
      return 1 / 0;
    if (t++, !cx.has(i) && (typeof e[i] == "object" && (0, ax.eachItem)(e[i], (o) => t += M_(o)), t === 1 / 0))
      return 1 / 0;
  }
  return t;
}
function L_(e, t = "", i) {
  i !== !1 && (t = fo(t));
  const o = e.parse(t);
  return U_(e, o);
}
Ot.getFullPath = L_;
function U_(e, t) {
  return e.serialize(t).split("#")[0] + "#";
}
Ot._getFullPath = U_;
const px = /#\/?$/;
function fo(e) {
  return e ? e.replace(px, "") : "";
}
Ot.normalizeId = fo;
function hx(e, t, i) {
  return i = fo(i), e.resolve(t, i);
}
Ot.resolveUrl = hx;
const mx = /^[a-z_][-a-z0-9._]*$/i;
function yx(e, t) {
  if (typeof e == "boolean")
    return {};
  const { schemaId: i, uriResolver: o } = this.opts, a = fo(e[i] || t), l = { "": a }, c = L_(o, a, !1), f = {}, d = /* @__PURE__ */ new Set();
  return ux(e, { allKeys: !0 }, (h, S, $, v) => {
    if (v === void 0)
      return;
    const w = c + S;
    let _ = l[v];
    typeof h[i] == "string" && (_ = E.call(this, h[i])), k.call(this, h.$anchor), k.call(this, h.$dynamicAnchor), l[S] = _;
    function E(j) {
      const T = this.opts.uriResolver.resolve;
      if (j = fo(_ ? T(_, j) : j), d.has(j))
        throw y(j);
      d.add(j);
      let N = this.refs[j];
      return typeof N == "string" && (N = this.refs[N]), typeof N == "object" ? m(h, N.schema, j) : j !== fo(w) && (j[0] === "#" ? (m(h, f[j], j), f[j] = h) : this.refs[j] = w), j;
    }
    function k(j) {
      if (typeof j == "string") {
        if (!mx.test(j))
          throw new Error(`invalid anchor "${j}"`);
        E.call(this, `#${j}`);
      }
    }
  }), f;
  function m(h, S, $) {
    if (S !== void 0 && !lx(h, S))
      throw y($);
  }
  function y(h) {
    return new Error(`reference "${h}" resolves to more than one schema`);
  }
}
Ot.getSchemaRefs = yx;
Object.defineProperty(wn, "__esModule", { value: !0 });
wn.getData = wn.KeywordCxt = wn.validateFunctionCode = void 0;
const z_ = vo, Wg = mt, Kd = tr, Dl = mt, gx = tu, Ps = Ln, Sf = Lr, _e = Te, Pe = Kn, vx = Ot, nr = he, hs = Xs;
function _x(e) {
  if (K_(e) && (W_(e), B_(e))) {
    Ex(e);
    return;
  }
  V_(e, () => (0, z_.topBoolOrEmptySchema)(e));
}
wn.validateFunctionCode = _x;
function V_({ gen: e, validateName: t, schema: i, schemaEnv: o, opts: a }, l) {
  a.code.es5 ? e.func(t, (0, _e._)`${Pe.default.data}, ${Pe.default.valCxt}`, o.$async, () => {
    e.code((0, _e._)`"use strict"; ${Hg(i, a)}`), wx(e, a), e.code(l);
  }) : e.func(t, (0, _e._)`${Pe.default.data}, ${Sx(a)}`, o.$async, () => e.code(Hg(i, a)).code(l));
}
function Sx(e) {
  return (0, _e._)`{${Pe.default.instancePath}="", ${Pe.default.parentData}, ${Pe.default.parentDataProperty}, ${Pe.default.rootData}=${Pe.default.data}${e.dynamicRef ? (0, _e._)`, ${Pe.default.dynamicAnchors}={}` : _e.nil}}={}`;
}
function wx(e, t) {
  e.if(Pe.default.valCxt, () => {
    e.var(Pe.default.instancePath, (0, _e._)`${Pe.default.valCxt}.${Pe.default.instancePath}`), e.var(Pe.default.parentData, (0, _e._)`${Pe.default.valCxt}.${Pe.default.parentData}`), e.var(Pe.default.parentDataProperty, (0, _e._)`${Pe.default.valCxt}.${Pe.default.parentDataProperty}`), e.var(Pe.default.rootData, (0, _e._)`${Pe.default.valCxt}.${Pe.default.rootData}`), t.dynamicRef && e.var(Pe.default.dynamicAnchors, (0, _e._)`${Pe.default.valCxt}.${Pe.default.dynamicAnchors}`);
  }, () => {
    e.var(Pe.default.instancePath, (0, _e._)`""`), e.var(Pe.default.parentData, (0, _e._)`undefined`), e.var(Pe.default.parentDataProperty, (0, _e._)`undefined`), e.var(Pe.default.rootData, Pe.default.data), t.dynamicRef && e.var(Pe.default.dynamicAnchors, (0, _e._)`{}`);
  });
}
function Ex(e) {
  const { schema: t, opts: i, gen: o } = e;
  V_(e, () => {
    i.$comment && t.$comment && q_(e), kx(e), o.let(Pe.default.vErrors, null), o.let(Pe.default.errors, 0), i.unevaluated && $x(e), H_(e), Ix(e);
  });
}
function $x(e) {
  const { gen: t, validateName: i } = e;
  e.evaluated = t.const("evaluated", (0, _e._)`${i}.evaluated`), t.if((0, _e._)`${e.evaluated}.dynamicProps`, () => t.assign((0, _e._)`${e.evaluated}.props`, (0, _e._)`undefined`)), t.if((0, _e._)`${e.evaluated}.dynamicItems`, () => t.assign((0, _e._)`${e.evaluated}.items`, (0, _e._)`undefined`));
}
function Hg(e, t) {
  const i = typeof e == "object" && e[t.schemaId];
  return i && (t.code.source || t.code.process) ? (0, _e._)`/*# sourceURL=${i} */` : _e.nil;
}
function Ox(e, t) {
  if (K_(e) && (W_(e), B_(e))) {
    Px(e, t);
    return;
  }
  (0, z_.boolOrEmptySchema)(e, t);
}
function B_({ schema: e, self: t }) {
  if (typeof e == "boolean")
    return !e;
  for (const i in e)
    if (t.RULES.all[i])
      return !0;
  return !1;
}
function K_(e) {
  return typeof e.schema != "boolean";
}
function Px(e, t) {
  const { schema: i, gen: o, opts: a } = e;
  a.$comment && i.$comment && q_(e), Tx(e), Nx(e);
  const l = o.const("_errs", Pe.default.errors);
  H_(e, l), o.var(t, (0, _e._)`${l} === ${Pe.default.errors}`);
}
function W_(e) {
  (0, nr.checkUnknownRules)(e), Cx(e);
}
function H_(e, t) {
  if (e.opts.jtd)
    return qg(e, [], !1, t);
  const i = (0, Wg.getSchemaTypes)(e.schema), o = (0, Wg.coerceAndCheckDataType)(e, i);
  qg(e, i, !o, t);
}
function Cx(e) {
  const { schema: t, errSchemaPath: i, opts: o, self: a } = e;
  t.$ref && o.ignoreKeywordsWithRef && (0, nr.schemaHasRulesButRef)(t, a.RULES) && a.logger.warn(`$ref: keywords ignored in schema at path "${i}"`);
}
function kx(e) {
  const { schema: t, opts: i } = e;
  t.default !== void 0 && i.useDefaults && i.strictSchema && (0, nr.checkStrictMode)(e, "default is ignored in the schema root");
}
function Tx(e) {
  const t = e.schema[e.opts.schemaId];
  t && (e.baseId = (0, vx.resolveUrl)(e.opts.uriResolver, e.baseId, t));
}
function Nx(e) {
  if (e.schema.$async && !e.schemaEnv.$async)
    throw new Error("async schema in sync schema");
}
function q_({ gen: e, schemaEnv: t, schema: i, errSchemaPath: o, opts: a }) {
  const l = i.$comment;
  if (a.$comment === !0)
    e.code((0, _e._)`${Pe.default.self}.logger.log(${l})`);
  else if (typeof a.$comment == "function") {
    const c = (0, _e.str)`${o}/$comment`, f = e.scopeValue("root", { ref: t.root });
    e.code((0, _e._)`${Pe.default.self}.opts.$comment(${l}, ${c}, ${f}.schema)`);
  }
}
function Ix(e) {
  const { gen: t, schemaEnv: i, validateName: o, ValidationError: a, opts: l } = e;
  i.$async ? t.if((0, _e._)`${Pe.default.errors} === 0`, () => t.return(Pe.default.data), () => t.throw((0, _e._)`new ${a}(${Pe.default.vErrors})`)) : (t.assign((0, _e._)`${o}.errors`, Pe.default.vErrors), l.unevaluated && jx(e), t.return((0, _e._)`${Pe.default.errors} === 0`));
}
function jx({ gen: e, evaluated: t, props: i, items: o }) {
  i instanceof _e.Name && e.assign((0, _e._)`${t}.props`, i), o instanceof _e.Name && e.assign((0, _e._)`${t}.items`, o);
}
function qg(e, t, i, o) {
  const { gen: a, schema: l, data: c, allErrors: f, opts: d, self: m } = e, { RULES: y } = m;
  if (l.$ref && (d.ignoreKeywordsWithRef || !(0, nr.schemaHasRulesButRef)(l, y))) {
    a.block(() => Q_(e, "$ref", y.all.$ref.definition));
    return;
  }
  d.jtd || Ax(e, t), a.block(() => {
    for (const S of y.rules)
      h(S);
    h(y.post);
  });
  function h(S) {
    (0, Kd.shouldUseGroup)(l, S) && (S.type ? (a.if((0, Dl.checkDataType)(S.type, c, d.strictNumbers)), Gg(e, S), t.length === 1 && t[0] === S.type && i && (a.else(), (0, Dl.reportTypeError)(e)), a.endIf()) : Gg(e, S), f || a.if((0, _e._)`${Pe.default.errors} === ${o || 0}`));
  }
}
function Gg(e, t) {
  const { gen: i, schema: o, opts: { useDefaults: a } } = e;
  a && (0, gx.assignDefaults)(e, t.type), i.block(() => {
    for (const l of t.rules)
      (0, Kd.shouldUseRule)(o, l) && Q_(e, l.keyword, l.definition, t.type);
  });
}
function Ax(e, t) {
  e.schemaEnv.meta || !e.opts.strictTypes || (xx(e, t), e.opts.allowUnionTypes || bx(e, t), Fx(e, e.dataTypes));
}
function xx(e, t) {
  if (t.length) {
    if (!e.dataTypes.length) {
      e.dataTypes = t;
      return;
    }
    t.forEach((i) => {
      G_(e.dataTypes, i) || Wd(e, `type "${i}" not allowed by context "${e.dataTypes.join(",")}"`);
    }), Dx(e, t);
  }
}
function bx(e, t) {
  t.length > 1 && !(t.length === 2 && t.includes("null")) && Wd(e, "use allowUnionTypes to allow union type keyword");
}
function Fx(e, t) {
  const i = e.self.RULES.all;
  for (const o in i) {
    const a = i[o];
    if (typeof a == "object" && (0, Kd.shouldUseRule)(e.schema, a)) {
      const { type: l } = a.definition;
      l.length && !l.some((c) => Rx(t, c)) && Wd(e, `missing type "${l.join(",")}" for keyword "${o}"`);
    }
  }
}
function Rx(e, t) {
  return e.includes(t) || t === "number" && e.includes("integer");
}
function G_(e, t) {
  return e.includes(t) || t === "integer" && e.includes("number");
}
function Dx(e, t) {
  const i = [];
  for (const o of e.dataTypes)
    G_(t, o) ? i.push(o) : t.includes("integer") && o === "number" && i.push("integer");
  e.dataTypes = i;
}
function Wd(e, t) {
  const i = e.schemaEnv.baseId + e.errSchemaPath;
  t += ` at "${i}" (strictTypes)`, (0, nr.checkStrictMode)(e, t, e.opts.strictTypes);
}
class Y_ {
  constructor(t, i, o) {
    if ((0, Ps.validateKeywordUsage)(t, i, o), this.gen = t.gen, this.allErrors = t.allErrors, this.keyword = o, this.data = t.data, this.schema = t.schema[o], this.$data = i.$data && t.opts.$data && this.schema && this.schema.$data, this.schemaValue = (0, nr.schemaRefOrVal)(t, this.schema, o, this.$data), this.schemaType = i.schemaType, this.parentSchema = t.schema, this.params = {}, this.it = t, this.def = i, this.$data)
      this.schemaCode = t.gen.const("vSchema", J_(this.$data, t));
    else if (this.schemaCode = this.schemaValue, !(0, Ps.validSchemaType)(this.schema, i.schemaType, i.allowUndefined))
      throw new Error(`${o} value must be ${JSON.stringify(i.schemaType)}`);
    ("code" in i ? i.trackErrors : i.errors !== !1) && (this.errsCount = t.gen.const("_errs", Pe.default.errors));
  }
  result(t, i, o) {
    this.failResult((0, _e.not)(t), i, o);
  }
  failResult(t, i, o) {
    this.gen.if(t), o ? o() : this.error(), i ? (this.gen.else(), i(), this.allErrors && this.gen.endIf()) : this.allErrors ? this.gen.endIf() : this.gen.else();
  }
  pass(t, i) {
    this.failResult((0, _e.not)(t), void 0, i);
  }
  fail(t) {
    if (t === void 0) {
      this.error(), this.allErrors || this.gen.if(!1);
      return;
    }
    this.gen.if(t), this.error(), this.allErrors ? this.gen.endIf() : this.gen.else();
  }
  fail$data(t) {
    if (!this.$data)
      return this.fail(t);
    const { schemaCode: i } = this;
    this.fail((0, _e._)`${i} !== undefined && (${(0, _e.or)(this.invalid$data(), t)})`);
  }
  error(t, i, o) {
    if (i) {
      this.setParams(i), this._error(t, o), this.setParams({});
      return;
    }
    this._error(t, o);
  }
  _error(t, i) {
    (t ? hs.reportExtraError : hs.reportError)(this, this.def.error, i);
  }
  $dataError() {
    (0, hs.reportError)(this, this.def.$dataError || hs.keyword$DataError);
  }
  reset() {
    if (this.errsCount === void 0)
      throw new Error('add "trackErrors" to keyword definition');
    (0, hs.resetErrorsCount)(this.gen, this.errsCount);
  }
  ok(t) {
    this.allErrors || this.gen.if(t);
  }
  setParams(t, i) {
    i ? Object.assign(this.params, t) : this.params = t;
  }
  block$data(t, i, o = _e.nil) {
    this.gen.block(() => {
      this.check$data(t, o), i();
    });
  }
  check$data(t = _e.nil, i = _e.nil) {
    if (!this.$data)
      return;
    const { gen: o, schemaCode: a, schemaType: l, def: c } = this;
    o.if((0, _e.or)((0, _e._)`${a} === undefined`, i)), t !== _e.nil && o.assign(t, !0), (l.length || c.validateSchema) && (o.elseIf(this.invalid$data()), this.$dataError(), t !== _e.nil && o.assign(t, !1)), o.else();
  }
  invalid$data() {
    const { gen: t, schemaCode: i, schemaType: o, def: a, it: l } = this;
    return (0, _e.or)(c(), f());
    function c() {
      if (o.length) {
        if (!(i instanceof _e.Name))
          throw new Error("ajv implementation error");
        const d = Array.isArray(o) ? o : [o];
        return (0, _e._)`${(0, Dl.checkDataTypes)(d, i, l.opts.strictNumbers, Dl.DataType.Wrong)}`;
      }
      return _e.nil;
    }
    function f() {
      if (a.validateSchema) {
        const d = t.scopeValue("validate$data", { ref: a.validateSchema });
        return (0, _e._)`!${d}(${i})`;
      }
      return _e.nil;
    }
  }
  subschema(t, i) {
    const o = (0, Sf.getSubschema)(this.it, t);
    (0, Sf.extendSubschemaData)(o, this.it, t), (0, Sf.extendSubschemaMode)(o, t);
    const a = { ...this.it, ...o, items: void 0, props: void 0 };
    return Ox(a, i), a;
  }
  mergeEvaluated(t, i) {
    const { it: o, gen: a } = this;
    o.opts.unevaluated && (o.props !== !0 && t.props !== void 0 && (o.props = nr.mergeEvaluated.props(a, t.props, o.props, i)), o.items !== !0 && t.items !== void 0 && (o.items = nr.mergeEvaluated.items(a, t.items, o.items, i)));
  }
  mergeValidEvaluated(t, i) {
    const { it: o, gen: a } = this;
    if (o.opts.unevaluated && (o.props !== !0 || o.items !== !0))
      return a.if(i, () => this.mergeEvaluated(t, _e.Name)), !0;
  }
}
wn.KeywordCxt = Y_;
function Q_(e, t, i, o) {
  const a = new Y_(e, i, t);
  "code" in i ? i.code(a, o) : a.$data && i.validate ? (0, Ps.funcKeywordCode)(a, i) : "macro" in i ? (0, Ps.macroKeywordCode)(a, i) : (i.compile || i.validate) && (0, Ps.funcKeywordCode)(a, i);
}
const Mx = /^\/(?:[^~]|~0|~1)*$/, Lx = /^([0-9]+)(#|\/(?:[^~]|~0|~1)*)?$/;
function J_(e, { dataLevel: t, dataNames: i, dataPathArr: o }) {
  let a, l;
  if (e === "")
    return Pe.default.rootData;
  if (e[0] === "/") {
    if (!Mx.test(e))
      throw new Error(`Invalid JSON-pointer: ${e}`);
    a = e, l = Pe.default.rootData;
  } else {
    const m = Lx.exec(e);
    if (!m)
      throw new Error(`Invalid JSON-pointer: ${e}`);
    const y = +m[1];
    if (a = m[2], a === "#") {
      if (y >= t)
        throw new Error(d("property/index", y));
      return o[t - y];
    }
    if (y > t)
      throw new Error(d("data", y));
    if (l = i[t - y], !a)
      return l;
  }
  let c = l;
  const f = a.split("/");
  for (const m of f)
    m && (l = (0, _e._)`${l}${(0, _e.getProperty)((0, nr.unescapeJsonPointer)(m))}`, c = (0, _e._)`${c} && ${l}`);
  return c;
  function d(m, y) {
    return `Cannot access ${m} ${y} levels up, current level is ${t}`;
  }
}
wn.getData = J_;
var fl = {}, Yg;
function Hd() {
  if (Yg) return fl;
  Yg = 1, Object.defineProperty(fl, "__esModule", { value: !0 });
  class e extends Error {
    constructor(i) {
      super("validation failed"), this.errors = i, this.ajv = this.validation = !0;
    }
  }
  return fl.default = e, fl;
}
var Oo = {};
Object.defineProperty(Oo, "__esModule", { value: !0 });
const wf = Ot;
class Ux extends Error {
  constructor(t, i, o, a) {
    super(a || `can't resolve reference ${o} from id ${i}`), this.missingRef = (0, wf.resolveUrl)(t, i, o), this.missingSchema = (0, wf.normalizeId)((0, wf.getFullPath)(t, this.missingRef));
  }
}
Oo.default = Ux;
var Kt = {};
Object.defineProperty(Kt, "__esModule", { value: !0 });
Kt.resolveSchema = Kt.getCompilingSchema = Kt.resolveRef = Kt.compileSchema = Kt.SchemaEnv = void 0;
const yn = Te, zx = Hd(), li = Kn, _n = Ot, Qg = he, Vx = wn;
class nu {
  constructor(t) {
    var i;
    this.refs = {}, this.dynamicAnchors = {};
    let o;
    typeof t.schema == "object" && (o = t.schema), this.schema = t.schema, this.schemaId = t.schemaId, this.root = t.root || this, this.baseId = (i = t.baseId) !== null && i !== void 0 ? i : (0, _n.normalizeId)(o == null ? void 0 : o[t.schemaId || "$id"]), this.schemaPath = t.schemaPath, this.localRefs = t.localRefs, this.meta = t.meta, this.$async = o == null ? void 0 : o.$async, this.refs = {};
  }
}
Kt.SchemaEnv = nu;
function qd(e) {
  const t = X_.call(this, e);
  if (t)
    return t;
  const i = (0, _n.getFullPath)(this.opts.uriResolver, e.root.baseId), { es5: o, lines: a } = this.opts.code, { ownProperties: l } = this.opts, c = new yn.CodeGen(this.scope, { es5: o, lines: a, ownProperties: l });
  let f;
  e.$async && (f = c.scopeValue("Error", {
    ref: zx.default,
    code: (0, yn._)`require("ajv/dist/runtime/validation_error").default`
  }));
  const d = c.scopeName("validate");
  e.validateName = d;
  const m = {
    gen: c,
    allErrors: this.opts.allErrors,
    data: li.default.data,
    parentData: li.default.parentData,
    parentDataProperty: li.default.parentDataProperty,
    dataNames: [li.default.data],
    dataPathArr: [yn.nil],
    // TODO can its length be used as dataLevel if nil is removed?
    dataLevel: 0,
    dataTypes: [],
    definedProperties: /* @__PURE__ */ new Set(),
    topSchemaRef: c.scopeValue("schema", this.opts.code.source === !0 ? { ref: e.schema, code: (0, yn.stringify)(e.schema) } : { ref: e.schema }),
    validateName: d,
    ValidationError: f,
    schema: e.schema,
    schemaEnv: e,
    rootId: i,
    baseId: e.baseId || i,
    schemaPath: yn.nil,
    errSchemaPath: e.schemaPath || (this.opts.jtd ? "" : "#"),
    errorPath: (0, yn._)`""`,
    opts: this.opts,
    self: this
  };
  let y;
  try {
    this._compilations.add(e), (0, Vx.validateFunctionCode)(m), c.optimize(this.opts.code.optimize);
    const h = c.toString();
    y = `${c.scopeRefs(li.default.scope)}return ${h}`, this.opts.code.process && (y = this.opts.code.process(y, e));
    const $ = new Function(`${li.default.self}`, `${li.default.scope}`, y)(this, this.scope.get());
    if (this.scope.value(d, { ref: $ }), $.errors = null, $.schema = e.schema, $.schemaEnv = e, e.$async && ($.$async = !0), this.opts.code.source === !0 && ($.source = { validateName: d, validateCode: h, scopeValues: c._values }), this.opts.unevaluated) {
      const { props: v, items: w } = m;
      $.evaluated = {
        props: v instanceof yn.Name ? void 0 : v,
        items: w instanceof yn.Name ? void 0 : w,
        dynamicProps: v instanceof yn.Name,
        dynamicItems: w instanceof yn.Name
      }, $.source && ($.source.evaluated = (0, yn.stringify)($.evaluated));
    }
    return e.validate = $, e;
  } catch (h) {
    throw delete e.validate, delete e.validateName, y && this.logger.error("Error compiling schema, function code:", y), h;
  } finally {
    this._compilations.delete(e);
  }
}
Kt.compileSchema = qd;
function Bx(e, t, i) {
  var o;
  i = (0, _n.resolveUrl)(this.opts.uriResolver, t, i);
  const a = e.refs[i];
  if (a)
    return a;
  let l = Hx.call(this, e, i);
  if (l === void 0) {
    const c = (o = e.localRefs) === null || o === void 0 ? void 0 : o[i], { schemaId: f } = this.opts;
    c && (l = new nu({ schema: c, schemaId: f, root: e, baseId: t }));
  }
  if (l !== void 0)
    return e.refs[i] = Kx.call(this, l);
}
Kt.resolveRef = Bx;
function Kx(e) {
  return (0, _n.inlineRef)(e.schema, this.opts.inlineRefs) ? e.schema : e.validate ? e : qd.call(this, e);
}
function X_(e) {
  for (const t of this._compilations)
    if (Wx(t, e))
      return t;
}
Kt.getCompilingSchema = X_;
function Wx(e, t) {
  return e.schema === t.schema && e.root === t.root && e.baseId === t.baseId;
}
function Hx(e, t) {
  let i;
  for (; typeof (i = this.refs[t]) == "string"; )
    t = i;
  return i || this.schemas[t] || ru.call(this, e, t);
}
function ru(e, t) {
  const i = this.opts.uriResolver.parse(t), o = (0, _n._getFullPath)(this.opts.uriResolver, i);
  let a = (0, _n.getFullPath)(this.opts.uriResolver, e.baseId, void 0);
  if (Object.keys(e.schema).length > 0 && o === a)
    return Ef.call(this, i, e);
  const l = (0, _n.normalizeId)(o), c = this.refs[l] || this.schemas[l];
  if (typeof c == "string") {
    const f = ru.call(this, e, c);
    return typeof (f == null ? void 0 : f.schema) != "object" ? void 0 : Ef.call(this, i, f);
  }
  if (typeof (c == null ? void 0 : c.schema) == "object") {
    if (c.validate || qd.call(this, c), l === (0, _n.normalizeId)(t)) {
      const { schema: f } = c, { schemaId: d } = this.opts, m = f[d];
      return m && (a = (0, _n.resolveUrl)(this.opts.uriResolver, a, m)), new nu({ schema: f, schemaId: d, root: e, baseId: a });
    }
    return Ef.call(this, i, c);
  }
}
Kt.resolveSchema = ru;
const qx = /* @__PURE__ */ new Set([
  "properties",
  "patternProperties",
  "enum",
  "dependencies",
  "definitions"
]);
function Ef(e, { baseId: t, schema: i, root: o }) {
  var a;
  if (((a = e.fragment) === null || a === void 0 ? void 0 : a[0]) !== "/")
    return;
  for (const f of e.fragment.slice(1).split("/")) {
    if (typeof i == "boolean")
      return;
    const d = i[(0, Qg.unescapeFragment)(f)];
    if (d === void 0)
      return;
    i = d;
    const m = typeof i == "object" && i[this.opts.schemaId];
    !qx.has(f) && m && (t = (0, _n.resolveUrl)(this.opts.uriResolver, t, m));
  }
  let l;
  if (typeof i != "boolean" && i.$ref && !(0, Qg.schemaHasRulesButRef)(i, this.RULES)) {
    const f = (0, _n.resolveUrl)(this.opts.uriResolver, t, i.$ref);
    l = ru.call(this, o, f);
  }
  const { schemaId: c } = this.opts;
  if (l = l || new nu({ schema: i, schemaId: c, root: o, baseId: t }), l.schema !== l.root.schema)
    return l;
}
const Gx = "https://raw.githubusercontent.com/ajv-validator/ajv/master/lib/refs/data.json#", Yx = "Meta-schema for $data reference (JSON AnySchema extension proposal)", Qx = "object", Jx = [
  "$data"
], Xx = {
  $data: {
    type: "string",
    anyOf: [
      {
        format: "relative-json-pointer"
      },
      {
        format: "json-pointer"
      }
    ]
  }
}, Zx = !1, eb = {
  $id: Gx,
  description: Yx,
  type: Qx,
  required: Jx,
  properties: Xx,
  additionalProperties: Zx
};
var Gd = {};
Object.defineProperty(Gd, "__esModule", { value: !0 });
const Z_ = O0;
Z_.code = 'require("ajv/dist/runtime/uri").default';
Gd.default = Z_;
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.CodeGen = e.Name = e.nil = e.stringify = e.str = e._ = e.KeywordCxt = void 0;
  var t = wn;
  Object.defineProperty(e, "KeywordCxt", { enumerable: !0, get: function() {
    return t.KeywordCxt;
  } });
  var i = Te;
  Object.defineProperty(e, "_", { enumerable: !0, get: function() {
    return i._;
  } }), Object.defineProperty(e, "str", { enumerable: !0, get: function() {
    return i.str;
  } }), Object.defineProperty(e, "stringify", { enumerable: !0, get: function() {
    return i.stringify;
  } }), Object.defineProperty(e, "nil", { enumerable: !0, get: function() {
    return i.nil;
  } }), Object.defineProperty(e, "Name", { enumerable: !0, get: function() {
    return i.Name;
  } }), Object.defineProperty(e, "CodeGen", { enumerable: !0, get: function() {
    return i.CodeGen;
  } });
  const o = Hd(), a = Oo, l = vi, c = Kt, f = Te, d = Ot, m = mt, y = he, h = eb, S = Gd, $ = (z, P) => new RegExp(z, P);
  $.code = "new RegExp";
  const v = ["removeAdditional", "useDefaults", "coerceTypes"], w = /* @__PURE__ */ new Set([
    "validate",
    "serialize",
    "parse",
    "wrapper",
    "root",
    "schema",
    "keyword",
    "pattern",
    "formats",
    "validate$data",
    "func",
    "obj",
    "Error"
  ]), _ = {
    errorDataPath: "",
    format: "`validateFormats: false` can be used instead.",
    nullable: '"nullable" keyword is supported by default.',
    jsonPointers: "Deprecated jsPropertySyntax can be used instead.",
    extendRefs: "Deprecated ignoreKeywordsWithRef can be used instead.",
    missingRefs: "Pass empty schema with $id that should be ignored to ajv.addSchema.",
    processCode: "Use option `code: {process: (code, schemaEnv: object) => string}`",
    sourceCode: "Use option `code: {source: true}`",
    strictDefaults: "It is default now, see option `strict`.",
    strictKeywords: "It is default now, see option `strict`.",
    uniqueItems: '"uniqueItems" keyword is always validated.',
    unknownFormats: "Disable strict mode or pass `true` to `ajv.addFormat` (or `formats` option).",
    cache: "Map is used as cache, schema object as key.",
    serialize: "Map is used as cache, schema object as key.",
    ajvErrors: "It is default now."
  }, E = {
    ignoreKeywordsWithRef: "",
    jsPropertySyntax: "",
    unicode: '"minLength"/"maxLength" account for unicode characters by default.'
  }, k = 200;
  function j(z) {
    var P, b, R, C, I, B, X, J, se, ce, $e, nt, ot, ze, Rt, et, Wt, Pt, Wn, $n, On, Br, ki, Ti, Ni;
    const lr = z.strict, Kr = (P = z.code) === null || P === void 0 ? void 0 : P.optimize, Wr = Kr === !0 || Kr === void 0 ? 1 : Kr || 0, ko = (R = (b = z.code) === null || b === void 0 ? void 0 : b.regExp) !== null && R !== void 0 ? R : $, Hr = (C = z.uriResolver) !== null && C !== void 0 ? C : S.default;
    return {
      strictSchema: (B = (I = z.strictSchema) !== null && I !== void 0 ? I : lr) !== null && B !== void 0 ? B : !0,
      strictNumbers: (J = (X = z.strictNumbers) !== null && X !== void 0 ? X : lr) !== null && J !== void 0 ? J : !0,
      strictTypes: (ce = (se = z.strictTypes) !== null && se !== void 0 ? se : lr) !== null && ce !== void 0 ? ce : "log",
      strictTuples: (nt = ($e = z.strictTuples) !== null && $e !== void 0 ? $e : lr) !== null && nt !== void 0 ? nt : "log",
      strictRequired: (ze = (ot = z.strictRequired) !== null && ot !== void 0 ? ot : lr) !== null && ze !== void 0 ? ze : !1,
      code: z.code ? { ...z.code, optimize: Wr, regExp: ko } : { optimize: Wr, regExp: ko },
      loopRequired: (Rt = z.loopRequired) !== null && Rt !== void 0 ? Rt : k,
      loopEnum: (et = z.loopEnum) !== null && et !== void 0 ? et : k,
      meta: (Wt = z.meta) !== null && Wt !== void 0 ? Wt : !0,
      messages: (Pt = z.messages) !== null && Pt !== void 0 ? Pt : !0,
      inlineRefs: (Wn = z.inlineRefs) !== null && Wn !== void 0 ? Wn : !0,
      schemaId: ($n = z.schemaId) !== null && $n !== void 0 ? $n : "$id",
      addUsedSchema: (On = z.addUsedSchema) !== null && On !== void 0 ? On : !0,
      validateSchema: (Br = z.validateSchema) !== null && Br !== void 0 ? Br : !0,
      validateFormats: (ki = z.validateFormats) !== null && ki !== void 0 ? ki : !0,
      unicodeRegExp: (Ti = z.unicodeRegExp) !== null && Ti !== void 0 ? Ti : !0,
      int32range: (Ni = z.int32range) !== null && Ni !== void 0 ? Ni : !0,
      uriResolver: Hr
    };
  }
  class T {
    constructor(P = {}) {
      this.schemas = {}, this.refs = {}, this.formats = {}, this._compilations = /* @__PURE__ */ new Set(), this._loading = {}, this._cache = /* @__PURE__ */ new Map(), P = this.opts = { ...P, ...j(P) };
      const { es5: b, lines: R } = this.opts.code;
      this.scope = new f.ValueScope({ scope: {}, prefixes: w, es5: b, lines: R }), this.logger = H(P.logger);
      const C = P.validateFormats;
      P.validateFormats = !1, this.RULES = (0, l.getRules)(), N.call(this, _, P, "NOT SUPPORTED"), N.call(this, E, P, "DEPRECATED", "warn"), this._metaOpts = G.call(this), P.formats && V.call(this), this._addVocabularies(), this._addDefaultMetaSchema(), P.keywords && U.call(this, P.keywords), typeof P.meta == "object" && this.addMetaSchema(P.meta), F.call(this), P.validateFormats = C;
    }
    _addVocabularies() {
      this.addKeyword("$async");
    }
    _addDefaultMetaSchema() {
      const { $data: P, meta: b, schemaId: R } = this.opts;
      let C = h;
      R === "id" && (C = { ...h }, C.id = C.$id, delete C.$id), b && P && this.addMetaSchema(C, C[R], !1);
    }
    defaultMeta() {
      const { meta: P, schemaId: b } = this.opts;
      return this.opts.defaultMeta = typeof P == "object" ? P[b] || P : void 0;
    }
    validate(P, b) {
      let R;
      if (typeof P == "string") {
        if (R = this.getSchema(P), !R)
          throw new Error(`no schema with key or ref "${P}"`);
      } else
        R = this.compile(P);
      const C = R(b);
      return "$async" in R || (this.errors = R.errors), C;
    }
    compile(P, b) {
      const R = this._addSchema(P, b);
      return R.validate || this._compileSchemaEnv(R);
    }
    compileAsync(P, b) {
      if (typeof this.opts.loadSchema != "function")
        throw new Error("options.loadSchema should be a function");
      const { loadSchema: R } = this.opts;
      return C.call(this, P, b);
      async function C(ce, $e) {
        await I.call(this, ce.$schema);
        const nt = this._addSchema(ce, $e);
        return nt.validate || B.call(this, nt);
      }
      async function I(ce) {
        ce && !this.getSchema(ce) && await C.call(this, { $ref: ce }, !0);
      }
      async function B(ce) {
        try {
          return this._compileSchemaEnv(ce);
        } catch ($e) {
          if (!($e instanceof a.default))
            throw $e;
          return X.call(this, $e), await J.call(this, $e.missingSchema), B.call(this, ce);
        }
      }
      function X({ missingSchema: ce, missingRef: $e }) {
        if (this.refs[ce])
          throw new Error(`AnySchema ${ce} is loaded but ${$e} cannot be resolved`);
      }
      async function J(ce) {
        const $e = await se.call(this, ce);
        this.refs[ce] || await I.call(this, $e.$schema), this.refs[ce] || this.addSchema($e, ce, b);
      }
      async function se(ce) {
        const $e = this._loading[ce];
        if ($e)
          return $e;
        try {
          return await (this._loading[ce] = R(ce));
        } finally {
          delete this._loading[ce];
        }
      }
    }
    // Adds schema to the instance
    addSchema(P, b, R, C = this.opts.validateSchema) {
      if (Array.isArray(P)) {
        for (const B of P)
          this.addSchema(B, void 0, R, C);
        return this;
      }
      let I;
      if (typeof P == "object") {
        const { schemaId: B } = this.opts;
        if (I = P[B], I !== void 0 && typeof I != "string")
          throw new Error(`schema ${B} must be string`);
      }
      return b = (0, d.normalizeId)(b || I), this._checkUnique(b), this.schemas[b] = this._addSchema(P, R, b, C, !0), this;
    }
    // Add schema that will be used to validate other schemas
    // options in META_IGNORE_OPTIONS are alway set to false
    addMetaSchema(P, b, R = this.opts.validateSchema) {
      return this.addSchema(P, b, !0, R), this;
    }
    //  Validate schema against its meta-schema
    validateSchema(P, b) {
      if (typeof P == "boolean")
        return !0;
      let R;
      if (R = P.$schema, R !== void 0 && typeof R != "string")
        throw new Error("$schema must be a string");
      if (R = R || this.opts.defaultMeta || this.defaultMeta(), !R)
        return this.logger.warn("meta-schema not available"), this.errors = null, !0;
      const C = this.validate(R, P);
      if (!C && b) {
        const I = "schema is invalid: " + this.errorsText();
        if (this.opts.validateSchema === "log")
          this.logger.error(I);
        else
          throw new Error(I);
      }
      return C;
    }
    // Get compiled schema by `key` or `ref`.
    // (`key` that was passed to `addSchema` or full schema reference - `schema.$id` or resolved id)
    getSchema(P) {
      let b;
      for (; typeof (b = x.call(this, P)) == "string"; )
        P = b;
      if (b === void 0) {
        const { schemaId: R } = this.opts, C = new c.SchemaEnv({ schema: {}, schemaId: R });
        if (b = c.resolveSchema.call(this, C, P), !b)
          return;
        this.refs[P] = b;
      }
      return b.validate || this._compileSchemaEnv(b);
    }
    // Remove cached schema(s).
    // If no parameter is passed all schemas but meta-schemas are removed.
    // If RegExp is passed all schemas with key/id matching pattern but meta-schemas are removed.
    // Even if schema is referenced by other schemas it still can be removed as other schemas have local references.
    removeSchema(P) {
      if (P instanceof RegExp)
        return this._removeAllSchemas(this.schemas, P), this._removeAllSchemas(this.refs, P), this;
      switch (typeof P) {
        case "undefined":
          return this._removeAllSchemas(this.schemas), this._removeAllSchemas(this.refs), this._cache.clear(), this;
        case "string": {
          const b = x.call(this, P);
          return typeof b == "object" && this._cache.delete(b.schema), delete this.schemas[P], delete this.refs[P], this;
        }
        case "object": {
          const b = P;
          this._cache.delete(b);
          let R = P[this.opts.schemaId];
          return R && (R = (0, d.normalizeId)(R), delete this.schemas[R], delete this.refs[R]), this;
        }
        default:
          throw new Error("ajv.removeSchema: invalid parameter");
      }
    }
    // add "vocabulary" - a collection of keywords
    addVocabulary(P) {
      for (const b of P)
        this.addKeyword(b);
      return this;
    }
    addKeyword(P, b) {
      let R;
      if (typeof P == "string")
        R = P, typeof b == "object" && (this.logger.warn("these parameters are deprecated, see docs for addKeyword"), b.keyword = R);
      else if (typeof P == "object" && b === void 0) {
        if (b = P, R = b.keyword, Array.isArray(R) && !R.length)
          throw new Error("addKeywords: keyword must be string or non-empty array");
      } else
        throw new Error("invalid addKeywords parameters");
      if (le.call(this, R, b), !b)
        return (0, y.eachItem)(R, (I) => ie.call(this, I)), this;
      pe.call(this, b);
      const C = {
        ...b,
        type: (0, m.getJSONTypes)(b.type),
        schemaType: (0, m.getJSONTypes)(b.schemaType)
      };
      return (0, y.eachItem)(R, C.type.length === 0 ? (I) => ie.call(this, I, C) : (I) => C.type.forEach((B) => ie.call(this, I, C, B))), this;
    }
    getKeyword(P) {
      const b = this.RULES.all[P];
      return typeof b == "object" ? b.definition : !!b;
    }
    // Remove keyword
    removeKeyword(P) {
      const { RULES: b } = this;
      delete b.keywords[P], delete b.all[P];
      for (const R of b.rules) {
        const C = R.rules.findIndex((I) => I.keyword === P);
        C >= 0 && R.rules.splice(C, 1);
      }
      return this;
    }
    // Add format
    addFormat(P, b) {
      return typeof b == "string" && (b = new RegExp(b)), this.formats[P] = b, this;
    }
    errorsText(P = this.errors, { separator: b = ", ", dataVar: R = "data" } = {}) {
      return !P || P.length === 0 ? "No errors" : P.map((C) => `${R}${C.instancePath} ${C.message}`).reduce((C, I) => C + b + I);
    }
    $dataMetaSchema(P, b) {
      const R = this.RULES.all;
      P = JSON.parse(JSON.stringify(P));
      for (const C of b) {
        const I = C.split("/").slice(1);
        let B = P;
        for (const X of I)
          B = B[X];
        for (const X in R) {
          const J = R[X];
          if (typeof J != "object")
            continue;
          const { $data: se } = J.definition, ce = B[X];
          se && ce && (B[X] = ae(ce));
        }
      }
      return P;
    }
    _removeAllSchemas(P, b) {
      for (const R in P) {
        const C = P[R];
        (!b || b.test(R)) && (typeof C == "string" ? delete P[R] : C && !C.meta && (this._cache.delete(C.schema), delete P[R]));
      }
    }
    _addSchema(P, b, R, C = this.opts.validateSchema, I = this.opts.addUsedSchema) {
      let B;
      const { schemaId: X } = this.opts;
      if (typeof P == "object")
        B = P[X];
      else {
        if (this.opts.jtd)
          throw new Error("schema must be object");
        if (typeof P != "boolean")
          throw new Error("schema must be object or boolean");
      }
      let J = this._cache.get(P);
      if (J !== void 0)
        return J;
      R = (0, d.normalizeId)(B || R);
      const se = d.getSchemaRefs.call(this, P, R);
      return J = new c.SchemaEnv({ schema: P, schemaId: X, meta: b, baseId: R, localRefs: se }), this._cache.set(J.schema, J), I && !R.startsWith("#") && (R && this._checkUnique(R), this.refs[R] = J), C && this.validateSchema(P, !0), J;
    }
    _checkUnique(P) {
      if (this.schemas[P] || this.refs[P])
        throw new Error(`schema with key or id "${P}" already exists`);
    }
    _compileSchemaEnv(P) {
      if (P.meta ? this._compileMetaSchema(P) : c.compileSchema.call(this, P), !P.validate)
        throw new Error("ajv implementation error");
      return P.validate;
    }
    _compileMetaSchema(P) {
      const b = this.opts;
      this.opts = this._metaOpts;
      try {
        c.compileSchema.call(this, P);
      } finally {
        this.opts = b;
      }
    }
  }
  T.ValidationError = o.default, T.MissingRefError = a.default, e.default = T;
  function N(z, P, b, R = "error") {
    for (const C in z) {
      const I = C;
      I in P && this.logger[R](`${b}: option ${C}. ${z[I]}`);
    }
  }
  function x(z) {
    return z = (0, d.normalizeId)(z), this.schemas[z] || this.refs[z];
  }
  function F() {
    const z = this.opts.schemas;
    if (z)
      if (Array.isArray(z))
        this.addSchema(z);
      else
        for (const P in z)
          this.addSchema(z[P], P);
  }
  function V() {
    for (const z in this.opts.formats) {
      const P = this.opts.formats[z];
      P && this.addFormat(z, P);
    }
  }
  function U(z) {
    if (Array.isArray(z)) {
      this.addVocabulary(z);
      return;
    }
    this.logger.warn("keywords option as map is deprecated, pass array");
    for (const P in z) {
      const b = z[P];
      b.keyword || (b.keyword = P), this.addKeyword(b);
    }
  }
  function G() {
    const z = { ...this.opts };
    for (const P of v)
      delete z[P];
    return z;
  }
  const Q = { log() {
  }, warn() {
  }, error() {
  } };
  function H(z) {
    if (z === !1)
      return Q;
    if (z === void 0)
      return console;
    if (z.log && z.warn && z.error)
      return z;
    throw new Error("logger must implement log, warn and error methods");
  }
  const q = /^[a-z_$][a-z0-9_$:-]*$/i;
  function le(z, P) {
    const { RULES: b } = this;
    if ((0, y.eachItem)(z, (R) => {
      if (b.keywords[R])
        throw new Error(`Keyword ${R} is already defined`);
      if (!q.test(R))
        throw new Error(`Keyword ${R} has invalid name`);
    }), !!P && P.$data && !("code" in P || "validate" in P))
      throw new Error('$data keyword must have "code" or "validate" function');
  }
  function ie(z, P, b) {
    var R;
    const C = P == null ? void 0 : P.post;
    if (b && C)
      throw new Error('keyword with "post" flag cannot have "type"');
    const { RULES: I } = this;
    let B = C ? I.post : I.rules.find(({ type: J }) => J === b);
    if (B || (B = { type: b, rules: [] }, I.rules.push(B)), I.keywords[z] = !0, !P)
      return;
    const X = {
      keyword: z,
      definition: {
        ...P,
        type: (0, m.getJSONTypes)(P.type),
        schemaType: (0, m.getJSONTypes)(P.schemaType)
      }
    };
    P.before ? ne.call(this, B, X, P.before) : B.rules.push(X), I.all[z] = X, (R = P.implements) === null || R === void 0 || R.forEach((J) => this.addKeyword(J));
  }
  function ne(z, P, b) {
    const R = z.rules.findIndex((C) => C.keyword === b);
    R >= 0 ? z.rules.splice(R, 0, P) : (z.rules.push(P), this.logger.warn(`rule ${b} is not defined`));
  }
  function pe(z) {
    let { metaSchema: P } = z;
    P !== void 0 && (z.$data && this.opts.$data && (P = ae(P)), z.validateSchema = this.compile(P, !0));
  }
  const Z = {
    $ref: "https://raw.githubusercontent.com/ajv-validator/ajv/master/lib/refs/data.json#"
  };
  function ae(z) {
    return { anyOf: [z, Z] };
  }
})(S_);
var Yd = {}, Qd = {}, Jd = {};
Object.defineProperty(Jd, "__esModule", { value: !0 });
const tb = {
  keyword: "id",
  code() {
    throw new Error('NOT SUPPORTED: keyword "id", use "$id" for schema ID');
  }
};
Jd.default = tb;
var _i = {};
Object.defineProperty(_i, "__esModule", { value: !0 });
_i.callRef = _i.getValidate = void 0;
const nb = Oo, Jg = je, Bt = Te, ro = Kn, Xg = Kt, dl = he, rb = {
  keyword: "$ref",
  schemaType: "string",
  code(e) {
    const { gen: t, schema: i, it: o } = e, { baseId: a, schemaEnv: l, validateName: c, opts: f, self: d } = o, { root: m } = l;
    if ((i === "#" || i === "#/") && a === m.baseId)
      return h();
    const y = Xg.resolveRef.call(d, m, a, i);
    if (y === void 0)
      throw new nb.default(o.opts.uriResolver, a, i);
    if (y instanceof Xg.SchemaEnv)
      return S(y);
    return $(y);
    function h() {
      if (l === m)
        return kl(e, c, l, l.$async);
      const v = t.scopeValue("root", { ref: m });
      return kl(e, (0, Bt._)`${v}.validate`, m, m.$async);
    }
    function S(v) {
      const w = eS(e, v);
      kl(e, w, v, v.$async);
    }
    function $(v) {
      const w = t.scopeValue("schema", f.code.source === !0 ? { ref: v, code: (0, Bt.stringify)(v) } : { ref: v }), _ = t.name("valid"), E = e.subschema({
        schema: v,
        dataTypes: [],
        schemaPath: Bt.nil,
        topSchemaRef: w,
        errSchemaPath: i
      }, _);
      e.mergeEvaluated(E), e.ok(_);
    }
  }
};
function eS(e, t) {
  const { gen: i } = e;
  return t.validate ? i.scopeValue("validate", { ref: t.validate }) : (0, Bt._)`${i.scopeValue("wrapper", { ref: t })}.validate`;
}
_i.getValidate = eS;
function kl(e, t, i, o) {
  const { gen: a, it: l } = e, { allErrors: c, schemaEnv: f, opts: d } = l, m = d.passContext ? ro.default.this : Bt.nil;
  o ? y() : h();
  function y() {
    if (!f.$async)
      throw new Error("async schema referenced by sync schema");
    const v = a.let("valid");
    a.try(() => {
      a.code((0, Bt._)`await ${(0, Jg.callValidateCode)(e, t, m)}`), $(t), c || a.assign(v, !0);
    }, (w) => {
      a.if((0, Bt._)`!(${w} instanceof ${l.ValidationError})`, () => a.throw(w)), S(w), c || a.assign(v, !1);
    }), e.ok(v);
  }
  function h() {
    e.result((0, Jg.callValidateCode)(e, t, m), () => $(t), () => S(t));
  }
  function S(v) {
    const w = (0, Bt._)`${v}.errors`;
    a.assign(ro.default.vErrors, (0, Bt._)`${ro.default.vErrors} === null ? ${w} : ${ro.default.vErrors}.concat(${w})`), a.assign(ro.default.errors, (0, Bt._)`${ro.default.vErrors}.length`);
  }
  function $(v) {
    var w;
    if (!l.opts.unevaluated)
      return;
    const _ = (w = i == null ? void 0 : i.validate) === null || w === void 0 ? void 0 : w.evaluated;
    if (l.props !== !0)
      if (_ && !_.dynamicProps)
        _.props !== void 0 && (l.props = dl.mergeEvaluated.props(a, _.props, l.props));
      else {
        const E = a.var("props", (0, Bt._)`${v}.evaluated.props`);
        l.props = dl.mergeEvaluated.props(a, E, l.props, Bt.Name);
      }
    if (l.items !== !0)
      if (_ && !_.dynamicItems)
        _.items !== void 0 && (l.items = dl.mergeEvaluated.items(a, _.items, l.items));
      else {
        const E = a.var("items", (0, Bt._)`${v}.evaluated.items`);
        l.items = dl.mergeEvaluated.items(a, E, l.items, Bt.Name);
      }
  }
}
_i.callRef = kl;
_i.default = rb;
Object.defineProperty(Qd, "__esModule", { value: !0 });
const ib = Jd, ob = _i, sb = [
  "$schema",
  "$id",
  "$defs",
  "$vocabulary",
  { keyword: "$comment" },
  "definitions",
  ib.default,
  ob.default
];
Qd.default = sb;
var Xd = {}, Zd = {};
Object.defineProperty(Zd, "__esModule", { value: !0 });
const Ml = Te, Ir = Ml.operators, Ll = {
  maximum: { okStr: "<=", ok: Ir.LTE, fail: Ir.GT },
  minimum: { okStr: ">=", ok: Ir.GTE, fail: Ir.LT },
  exclusiveMaximum: { okStr: "<", ok: Ir.LT, fail: Ir.GTE },
  exclusiveMinimum: { okStr: ">", ok: Ir.GT, fail: Ir.LTE }
}, ab = {
  message: ({ keyword: e, schemaCode: t }) => (0, Ml.str)`must be ${Ll[e].okStr} ${t}`,
  params: ({ keyword: e, schemaCode: t }) => (0, Ml._)`{comparison: ${Ll[e].okStr}, limit: ${t}}`
}, lb = {
  keyword: Object.keys(Ll),
  type: "number",
  schemaType: "number",
  $data: !0,
  error: ab,
  code(e) {
    const { keyword: t, data: i, schemaCode: o } = e;
    e.fail$data((0, Ml._)`${i} ${Ll[t].fail} ${o} || isNaN(${i})`);
  }
};
Zd.default = lb;
var ep = {};
Object.defineProperty(ep, "__esModule", { value: !0 });
const Cs = Te, ub = {
  message: ({ schemaCode: e }) => (0, Cs.str)`must be multiple of ${e}`,
  params: ({ schemaCode: e }) => (0, Cs._)`{multipleOf: ${e}}`
}, cb = {
  keyword: "multipleOf",
  type: "number",
  schemaType: "number",
  $data: !0,
  error: ub,
  code(e) {
    const { gen: t, data: i, schemaCode: o, it: a } = e, l = a.opts.multipleOfPrecision, c = t.let("res"), f = l ? (0, Cs._)`Math.abs(Math.round(${c}) - ${c}) > 1e-${l}` : (0, Cs._)`${c} !== parseInt(${c})`;
    e.fail$data((0, Cs._)`(${o} === 0 || (${c} = ${i}/${o}, ${f}))`);
  }
};
ep.default = cb;
var tp = {}, np = {};
Object.defineProperty(np, "__esModule", { value: !0 });
function tS(e) {
  const t = e.length;
  let i = 0, o = 0, a;
  for (; o < t; )
    i++, a = e.charCodeAt(o++), a >= 55296 && a <= 56319 && o < t && (a = e.charCodeAt(o), (a & 64512) === 56320 && o++);
  return i;
}
np.default = tS;
tS.code = 'require("ajv/dist/runtime/ucs2length").default';
Object.defineProperty(tp, "__esModule", { value: !0 });
const fi = Te, fb = he, db = np, pb = {
  message({ keyword: e, schemaCode: t }) {
    const i = e === "maxLength" ? "more" : "fewer";
    return (0, fi.str)`must NOT have ${i} than ${t} characters`;
  },
  params: ({ schemaCode: e }) => (0, fi._)`{limit: ${e}}`
}, hb = {
  keyword: ["maxLength", "minLength"],
  type: "string",
  schemaType: "number",
  $data: !0,
  error: pb,
  code(e) {
    const { keyword: t, data: i, schemaCode: o, it: a } = e, l = t === "maxLength" ? fi.operators.GT : fi.operators.LT, c = a.opts.unicode === !1 ? (0, fi._)`${i}.length` : (0, fi._)`${(0, fb.useFunc)(e.gen, db.default)}(${i})`;
    e.fail$data((0, fi._)`${c} ${l} ${o}`);
  }
};
tp.default = hb;
var rp = {};
Object.defineProperty(rp, "__esModule", { value: !0 });
const mb = je, Ul = Te, yb = {
  message: ({ schemaCode: e }) => (0, Ul.str)`must match pattern "${e}"`,
  params: ({ schemaCode: e }) => (0, Ul._)`{pattern: ${e}}`
}, gb = {
  keyword: "pattern",
  type: "string",
  schemaType: "string",
  $data: !0,
  error: yb,
  code(e) {
    const { data: t, $data: i, schema: o, schemaCode: a, it: l } = e, c = l.opts.unicodeRegExp ? "u" : "", f = i ? (0, Ul._)`(new RegExp(${a}, ${c}))` : (0, mb.usePattern)(e, o);
    e.fail$data((0, Ul._)`!${f}.test(${t})`);
  }
};
rp.default = gb;
var ip = {};
Object.defineProperty(ip, "__esModule", { value: !0 });
const ks = Te, vb = {
  message({ keyword: e, schemaCode: t }) {
    const i = e === "maxProperties" ? "more" : "fewer";
    return (0, ks.str)`must NOT have ${i} than ${t} properties`;
  },
  params: ({ schemaCode: e }) => (0, ks._)`{limit: ${e}}`
}, _b = {
  keyword: ["maxProperties", "minProperties"],
  type: "object",
  schemaType: "number",
  $data: !0,
  error: vb,
  code(e) {
    const { keyword: t, data: i, schemaCode: o } = e, a = t === "maxProperties" ? ks.operators.GT : ks.operators.LT;
    e.fail$data((0, ks._)`Object.keys(${i}).length ${a} ${o}`);
  }
};
ip.default = _b;
var op = {};
Object.defineProperty(op, "__esModule", { value: !0 });
const ms = je, Ts = Te, Sb = he, wb = {
  message: ({ params: { missingProperty: e } }) => (0, Ts.str)`must have required property '${e}'`,
  params: ({ params: { missingProperty: e } }) => (0, Ts._)`{missingProperty: ${e}}`
}, Eb = {
  keyword: "required",
  type: "object",
  schemaType: "array",
  $data: !0,
  error: wb,
  code(e) {
    const { gen: t, schema: i, schemaCode: o, data: a, $data: l, it: c } = e, { opts: f } = c;
    if (!l && i.length === 0)
      return;
    const d = i.length >= f.loopRequired;
    if (c.allErrors ? m() : y(), f.strictRequired) {
      const $ = e.parentSchema.properties, { definedProperties: v } = e.it;
      for (const w of i)
        if (($ == null ? void 0 : $[w]) === void 0 && !v.has(w)) {
          const _ = c.schemaEnv.baseId + c.errSchemaPath, E = `required property "${w}" is not defined at "${_}" (strictRequired)`;
          (0, Sb.checkStrictMode)(c, E, c.opts.strictRequired);
        }
    }
    function m() {
      if (d || l)
        e.block$data(Ts.nil, h);
      else
        for (const $ of i)
          (0, ms.checkReportMissingProp)(e, $);
    }
    function y() {
      const $ = t.let("missing");
      if (d || l) {
        const v = t.let("valid", !0);
        e.block$data(v, () => S($, v)), e.ok(v);
      } else
        t.if((0, ms.checkMissingProp)(e, i, $)), (0, ms.reportMissingProp)(e, $), t.else();
    }
    function h() {
      t.forOf("prop", o, ($) => {
        e.setParams({ missingProperty: $ }), t.if((0, ms.noPropertyInData)(t, a, $, f.ownProperties), () => e.error());
      });
    }
    function S($, v) {
      e.setParams({ missingProperty: $ }), t.forOf($, o, () => {
        t.assign(v, (0, ms.propertyInData)(t, a, $, f.ownProperties)), t.if((0, Ts.not)(v), () => {
          e.error(), t.break();
        });
      }, Ts.nil);
    }
  }
};
op.default = Eb;
var sp = {};
Object.defineProperty(sp, "__esModule", { value: !0 });
const Ns = Te, $b = {
  message({ keyword: e, schemaCode: t }) {
    const i = e === "maxItems" ? "more" : "fewer";
    return (0, Ns.str)`must NOT have ${i} than ${t} items`;
  },
  params: ({ schemaCode: e }) => (0, Ns._)`{limit: ${e}}`
}, Ob = {
  keyword: ["maxItems", "minItems"],
  type: "array",
  schemaType: "number",
  $data: !0,
  error: $b,
  code(e) {
    const { keyword: t, data: i, schemaCode: o } = e, a = t === "maxItems" ? Ns.operators.GT : Ns.operators.LT;
    e.fail$data((0, Ns._)`${i}.length ${a} ${o}`);
  }
};
sp.default = Ob;
var ap = {}, Zs = {};
Object.defineProperty(Zs, "__esModule", { value: !0 });
const nS = R_;
nS.code = 'require("ajv/dist/runtime/equal").default';
Zs.default = nS;
Object.defineProperty(ap, "__esModule", { value: !0 });
const $f = mt, Et = Te, Pb = he, Cb = Zs, kb = {
  message: ({ params: { i: e, j: t } }) => (0, Et.str)`must NOT have duplicate items (items ## ${t} and ${e} are identical)`,
  params: ({ params: { i: e, j: t } }) => (0, Et._)`{i: ${e}, j: ${t}}`
}, Tb = {
  keyword: "uniqueItems",
  type: "array",
  schemaType: "boolean",
  $data: !0,
  error: kb,
  code(e) {
    const { gen: t, data: i, $data: o, schema: a, parentSchema: l, schemaCode: c, it: f } = e;
    if (!o && !a)
      return;
    const d = t.let("valid"), m = l.items ? (0, $f.getSchemaTypes)(l.items) : [];
    e.block$data(d, y, (0, Et._)`${c} === false`), e.ok(d);
    function y() {
      const v = t.let("i", (0, Et._)`${i}.length`), w = t.let("j");
      e.setParams({ i: v, j: w }), t.assign(d, !0), t.if((0, Et._)`${v} > 1`, () => (h() ? S : $)(v, w));
    }
    function h() {
      return m.length > 0 && !m.some((v) => v === "object" || v === "array");
    }
    function S(v, w) {
      const _ = t.name("item"), E = (0, $f.checkDataTypes)(m, _, f.opts.strictNumbers, $f.DataType.Wrong), k = t.const("indices", (0, Et._)`{}`);
      t.for((0, Et._)`;${v}--;`, () => {
        t.let(_, (0, Et._)`${i}[${v}]`), t.if(E, (0, Et._)`continue`), m.length > 1 && t.if((0, Et._)`typeof ${_} == "string"`, (0, Et._)`${_} += "_"`), t.if((0, Et._)`typeof ${k}[${_}] == "number"`, () => {
          t.assign(w, (0, Et._)`${k}[${_}]`), e.error(), t.assign(d, !1).break();
        }).code((0, Et._)`${k}[${_}] = ${v}`);
      });
    }
    function $(v, w) {
      const _ = (0, Pb.useFunc)(t, Cb.default), E = t.name("outer");
      t.label(E).for((0, Et._)`;${v}--;`, () => t.for((0, Et._)`${w} = ${v}; ${w}--;`, () => t.if((0, Et._)`${_}(${i}[${v}], ${i}[${w}])`, () => {
        e.error(), t.assign(d, !1).break(E);
      })));
    }
  }
};
ap.default = Tb;
var lp = {};
Object.defineProperty(lp, "__esModule", { value: !0 });
const qf = Te, Nb = he, Ib = Zs, jb = {
  message: "must be equal to constant",
  params: ({ schemaCode: e }) => (0, qf._)`{allowedValue: ${e}}`
}, Ab = {
  keyword: "const",
  $data: !0,
  error: jb,
  code(e) {
    const { gen: t, data: i, $data: o, schemaCode: a, schema: l } = e;
    o || l && typeof l == "object" ? e.fail$data((0, qf._)`!${(0, Nb.useFunc)(t, Ib.default)}(${i}, ${a})`) : e.fail((0, qf._)`${l} !== ${i}`);
  }
};
lp.default = Ab;
var up = {};
Object.defineProperty(up, "__esModule", { value: !0 });
const Ss = Te, xb = he, bb = Zs, Fb = {
  message: "must be equal to one of the allowed values",
  params: ({ schemaCode: e }) => (0, Ss._)`{allowedValues: ${e}}`
}, Rb = {
  keyword: "enum",
  schemaType: "array",
  $data: !0,
  error: Fb,
  code(e) {
    const { gen: t, data: i, $data: o, schema: a, schemaCode: l, it: c } = e;
    if (!o && a.length === 0)
      throw new Error("enum must have non-empty array");
    const f = a.length >= c.opts.loopEnum;
    let d;
    const m = () => d ?? (d = (0, xb.useFunc)(t, bb.default));
    let y;
    if (f || o)
      y = t.let("valid"), e.block$data(y, h);
    else {
      if (!Array.isArray(a))
        throw new Error("ajv implementation error");
      const $ = t.const("vSchema", l);
      y = (0, Ss.or)(...a.map((v, w) => S($, w)));
    }
    e.pass(y);
    function h() {
      t.assign(y, !1), t.forOf("v", l, ($) => t.if((0, Ss._)`${m()}(${i}, ${$})`, () => t.assign(y, !0).break()));
    }
    function S($, v) {
      const w = a[v];
      return typeof w == "object" && w !== null ? (0, Ss._)`${m()}(${i}, ${$}[${v}])` : (0, Ss._)`${i} === ${w}`;
    }
  }
};
up.default = Rb;
Object.defineProperty(Xd, "__esModule", { value: !0 });
const Db = Zd, Mb = ep, Lb = tp, Ub = rp, zb = ip, Vb = op, Bb = sp, Kb = ap, Wb = lp, Hb = up, qb = [
  // number
  Db.default,
  Mb.default,
  // string
  Lb.default,
  Ub.default,
  // object
  zb.default,
  Vb.default,
  // array
  Bb.default,
  Kb.default,
  // any
  { keyword: "type", schemaType: ["string", "array"] },
  { keyword: "nullable", schemaType: "boolean" },
  Wb.default,
  Hb.default
];
Xd.default = qb;
var cp = {}, Po = {};
Object.defineProperty(Po, "__esModule", { value: !0 });
Po.validateAdditionalItems = void 0;
const di = Te, Gf = he, Gb = {
  message: ({ params: { len: e } }) => (0, di.str)`must NOT have more than ${e} items`,
  params: ({ params: { len: e } }) => (0, di._)`{limit: ${e}}`
}, Yb = {
  keyword: "additionalItems",
  type: "array",
  schemaType: ["boolean", "object"],
  before: "uniqueItems",
  error: Gb,
  code(e) {
    const { parentSchema: t, it: i } = e, { items: o } = t;
    if (!Array.isArray(o)) {
      (0, Gf.checkStrictMode)(i, '"additionalItems" is ignored when "items" is not an array of schemas');
      return;
    }
    rS(e, o);
  }
};
function rS(e, t) {
  const { gen: i, schema: o, data: a, keyword: l, it: c } = e;
  c.items = !0;
  const f = i.const("len", (0, di._)`${a}.length`);
  if (o === !1)
    e.setParams({ len: t.length }), e.pass((0, di._)`${f} <= ${t.length}`);
  else if (typeof o == "object" && !(0, Gf.alwaysValidSchema)(c, o)) {
    const m = i.var("valid", (0, di._)`${f} <= ${t.length}`);
    i.if((0, di.not)(m), () => d(m)), e.ok(m);
  }
  function d(m) {
    i.forRange("i", t.length, f, (y) => {
      e.subschema({ keyword: l, dataProp: y, dataPropType: Gf.Type.Num }, m), c.allErrors || i.if((0, di.not)(m), () => i.break());
    });
  }
}
Po.validateAdditionalItems = rS;
Po.default = Yb;
var fp = {}, Co = {};
Object.defineProperty(Co, "__esModule", { value: !0 });
Co.validateTuple = void 0;
const Zg = Te, Tl = he, Qb = je, Jb = {
  keyword: "items",
  type: "array",
  schemaType: ["object", "array", "boolean"],
  before: "uniqueItems",
  code(e) {
    const { schema: t, it: i } = e;
    if (Array.isArray(t))
      return iS(e, "additionalItems", t);
    i.items = !0, !(0, Tl.alwaysValidSchema)(i, t) && e.ok((0, Qb.validateArray)(e));
  }
};
function iS(e, t, i = e.schema) {
  const { gen: o, parentSchema: a, data: l, keyword: c, it: f } = e;
  y(a), f.opts.unevaluated && i.length && f.items !== !0 && (f.items = Tl.mergeEvaluated.items(o, i.length, f.items));
  const d = o.name("valid"), m = o.const("len", (0, Zg._)`${l}.length`);
  i.forEach((h, S) => {
    (0, Tl.alwaysValidSchema)(f, h) || (o.if((0, Zg._)`${m} > ${S}`, () => e.subschema({
      keyword: c,
      schemaProp: S,
      dataProp: S
    }, d)), e.ok(d));
  });
  function y(h) {
    const { opts: S, errSchemaPath: $ } = f, v = i.length, w = v === h.minItems && (v === h.maxItems || h[t] === !1);
    if (S.strictTuples && !w) {
      const _ = `"${c}" is ${v}-tuple, but minItems or maxItems/${t} are not specified or different at path "${$}"`;
      (0, Tl.checkStrictMode)(f, _, S.strictTuples);
    }
  }
}
Co.validateTuple = iS;
Co.default = Jb;
Object.defineProperty(fp, "__esModule", { value: !0 });
const Xb = Co, Zb = {
  keyword: "prefixItems",
  type: "array",
  schemaType: ["array"],
  before: "uniqueItems",
  code: (e) => (0, Xb.validateTuple)(e, "items")
};
fp.default = Zb;
var dp = {};
Object.defineProperty(dp, "__esModule", { value: !0 });
const ev = Te, e2 = he, t2 = je, n2 = Po, r2 = {
  message: ({ params: { len: e } }) => (0, ev.str)`must NOT have more than ${e} items`,
  params: ({ params: { len: e } }) => (0, ev._)`{limit: ${e}}`
}, i2 = {
  keyword: "items",
  type: "array",
  schemaType: ["object", "boolean"],
  before: "uniqueItems",
  error: r2,
  code(e) {
    const { schema: t, parentSchema: i, it: o } = e, { prefixItems: a } = i;
    o.items = !0, !(0, e2.alwaysValidSchema)(o, t) && (a ? (0, n2.validateAdditionalItems)(e, a) : e.ok((0, t2.validateArray)(e)));
  }
};
dp.default = i2;
var pp = {};
Object.defineProperty(pp, "__esModule", { value: !0 });
const nn = Te, pl = he, o2 = {
  message: ({ params: { min: e, max: t } }) => t === void 0 ? (0, nn.str)`must contain at least ${e} valid item(s)` : (0, nn.str)`must contain at least ${e} and no more than ${t} valid item(s)`,
  params: ({ params: { min: e, max: t } }) => t === void 0 ? (0, nn._)`{minContains: ${e}}` : (0, nn._)`{minContains: ${e}, maxContains: ${t}}`
}, s2 = {
  keyword: "contains",
  type: "array",
  schemaType: ["object", "boolean"],
  before: "uniqueItems",
  trackErrors: !0,
  error: o2,
  code(e) {
    const { gen: t, schema: i, parentSchema: o, data: a, it: l } = e;
    let c, f;
    const { minContains: d, maxContains: m } = o;
    l.opts.next ? (c = d === void 0 ? 1 : d, f = m) : c = 1;
    const y = t.const("len", (0, nn._)`${a}.length`);
    if (e.setParams({ min: c, max: f }), f === void 0 && c === 0) {
      (0, pl.checkStrictMode)(l, '"minContains" == 0 without "maxContains": "contains" keyword ignored');
      return;
    }
    if (f !== void 0 && c > f) {
      (0, pl.checkStrictMode)(l, '"minContains" > "maxContains" is always invalid'), e.fail();
      return;
    }
    if ((0, pl.alwaysValidSchema)(l, i)) {
      let w = (0, nn._)`${y} >= ${c}`;
      f !== void 0 && (w = (0, nn._)`${w} && ${y} <= ${f}`), e.pass(w);
      return;
    }
    l.items = !0;
    const h = t.name("valid");
    f === void 0 && c === 1 ? $(h, () => t.if(h, () => t.break())) : c === 0 ? (t.let(h, !0), f !== void 0 && t.if((0, nn._)`${a}.length > 0`, S)) : (t.let(h, !1), S()), e.result(h, () => e.reset());
    function S() {
      const w = t.name("_valid"), _ = t.let("count", 0);
      $(w, () => t.if(w, () => v(_)));
    }
    function $(w, _) {
      t.forRange("i", 0, y, (E) => {
        e.subschema({
          keyword: "contains",
          dataProp: E,
          dataPropType: pl.Type.Num,
          compositeRule: !0
        }, w), _();
      });
    }
    function v(w) {
      t.code((0, nn._)`${w}++`), f === void 0 ? t.if((0, nn._)`${w} >= ${c}`, () => t.assign(h, !0).break()) : (t.if((0, nn._)`${w} > ${f}`, () => t.assign(h, !1).break()), c === 1 ? t.assign(h, !0) : t.if((0, nn._)`${w} >= ${c}`, () => t.assign(h, !0)));
    }
  }
};
pp.default = s2;
var oS = {};
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.validateSchemaDeps = e.validatePropertyDeps = e.error = void 0;
  const t = Te, i = he, o = je;
  e.error = {
    message: ({ params: { property: d, depsCount: m, deps: y } }) => {
      const h = m === 1 ? "property" : "properties";
      return (0, t.str)`must have ${h} ${y} when property ${d} is present`;
    },
    params: ({ params: { property: d, depsCount: m, deps: y, missingProperty: h } }) => (0, t._)`{property: ${d},
    missingProperty: ${h},
    depsCount: ${m},
    deps: ${y}}`
    // TODO change to reference
  };
  const a = {
    keyword: "dependencies",
    type: "object",
    schemaType: "object",
    error: e.error,
    code(d) {
      const [m, y] = l(d);
      c(d, m), f(d, y);
    }
  };
  function l({ schema: d }) {
    const m = {}, y = {};
    for (const h in d) {
      if (h === "__proto__")
        continue;
      const S = Array.isArray(d[h]) ? m : y;
      S[h] = d[h];
    }
    return [m, y];
  }
  function c(d, m = d.schema) {
    const { gen: y, data: h, it: S } = d;
    if (Object.keys(m).length === 0)
      return;
    const $ = y.let("missing");
    for (const v in m) {
      const w = m[v];
      if (w.length === 0)
        continue;
      const _ = (0, o.propertyInData)(y, h, v, S.opts.ownProperties);
      d.setParams({
        property: v,
        depsCount: w.length,
        deps: w.join(", ")
      }), S.allErrors ? y.if(_, () => {
        for (const E of w)
          (0, o.checkReportMissingProp)(d, E);
      }) : (y.if((0, t._)`${_} && (${(0, o.checkMissingProp)(d, w, $)})`), (0, o.reportMissingProp)(d, $), y.else());
    }
  }
  e.validatePropertyDeps = c;
  function f(d, m = d.schema) {
    const { gen: y, data: h, keyword: S, it: $ } = d, v = y.name("valid");
    for (const w in m)
      (0, i.alwaysValidSchema)($, m[w]) || (y.if(
        (0, o.propertyInData)(y, h, w, $.opts.ownProperties),
        () => {
          const _ = d.subschema({ keyword: S, schemaProp: w }, v);
          d.mergeValidEvaluated(_, v);
        },
        () => y.var(v, !0)
        // TODO var
      ), d.ok(v));
  }
  e.validateSchemaDeps = f, e.default = a;
})(oS);
var hp = {};
Object.defineProperty(hp, "__esModule", { value: !0 });
const sS = Te, a2 = he, l2 = {
  message: "property name must be valid",
  params: ({ params: e }) => (0, sS._)`{propertyName: ${e.propertyName}}`
}, u2 = {
  keyword: "propertyNames",
  type: "object",
  schemaType: ["object", "boolean"],
  error: l2,
  code(e) {
    const { gen: t, schema: i, data: o, it: a } = e;
    if ((0, a2.alwaysValidSchema)(a, i))
      return;
    const l = t.name("valid");
    t.forIn("key", o, (c) => {
      e.setParams({ propertyName: c }), e.subschema({
        keyword: "propertyNames",
        data: c,
        dataTypes: ["string"],
        propertyName: c,
        compositeRule: !0
      }, l), t.if((0, sS.not)(l), () => {
        e.error(!0), a.allErrors || t.break();
      });
    }), e.ok(l);
  }
};
hp.default = u2;
var iu = {};
Object.defineProperty(iu, "__esModule", { value: !0 });
const hl = je, gn = Te, c2 = Kn, ml = he, f2 = {
  message: "must NOT have additional properties",
  params: ({ params: e }) => (0, gn._)`{additionalProperty: ${e.additionalProperty}}`
}, d2 = {
  keyword: "additionalProperties",
  type: ["object"],
  schemaType: ["boolean", "object"],
  allowUndefined: !0,
  trackErrors: !0,
  error: f2,
  code(e) {
    const { gen: t, schema: i, parentSchema: o, data: a, errsCount: l, it: c } = e;
    if (!l)
      throw new Error("ajv implementation error");
    const { allErrors: f, opts: d } = c;
    if (c.props = !0, d.removeAdditional !== "all" && (0, ml.alwaysValidSchema)(c, i))
      return;
    const m = (0, hl.allSchemaProperties)(o.properties), y = (0, hl.allSchemaProperties)(o.patternProperties);
    h(), e.ok((0, gn._)`${l} === ${c2.default.errors}`);
    function h() {
      t.forIn("key", a, (_) => {
        !m.length && !y.length ? v(_) : t.if(S(_), () => v(_));
      });
    }
    function S(_) {
      let E;
      if (m.length > 8) {
        const k = (0, ml.schemaRefOrVal)(c, o.properties, "properties");
        E = (0, hl.isOwnProperty)(t, k, _);
      } else m.length ? E = (0, gn.or)(...m.map((k) => (0, gn._)`${_} === ${k}`)) : E = gn.nil;
      return y.length && (E = (0, gn.or)(E, ...y.map((k) => (0, gn._)`${(0, hl.usePattern)(e, k)}.test(${_})`))), (0, gn.not)(E);
    }
    function $(_) {
      t.code((0, gn._)`delete ${a}[${_}]`);
    }
    function v(_) {
      if (d.removeAdditional === "all" || d.removeAdditional && i === !1) {
        $(_);
        return;
      }
      if (i === !1) {
        e.setParams({ additionalProperty: _ }), e.error(), f || t.break();
        return;
      }
      if (typeof i == "object" && !(0, ml.alwaysValidSchema)(c, i)) {
        const E = t.name("valid");
        d.removeAdditional === "failing" ? (w(_, E, !1), t.if((0, gn.not)(E), () => {
          e.reset(), $(_);
        })) : (w(_, E), f || t.if((0, gn.not)(E), () => t.break()));
      }
    }
    function w(_, E, k) {
      const j = {
        keyword: "additionalProperties",
        dataProp: _,
        dataPropType: ml.Type.Str
      };
      k === !1 && Object.assign(j, {
        compositeRule: !0,
        createErrors: !1,
        allErrors: !1
      }), e.subschema(j, E);
    }
  }
};
iu.default = d2;
var mp = {};
Object.defineProperty(mp, "__esModule", { value: !0 });
const p2 = wn, tv = je, Of = he, nv = iu, h2 = {
  keyword: "properties",
  type: "object",
  schemaType: "object",
  code(e) {
    const { gen: t, schema: i, parentSchema: o, data: a, it: l } = e;
    l.opts.removeAdditional === "all" && o.additionalProperties === void 0 && nv.default.code(new p2.KeywordCxt(l, nv.default, "additionalProperties"));
    const c = (0, tv.allSchemaProperties)(i);
    for (const h of c)
      l.definedProperties.add(h);
    l.opts.unevaluated && c.length && l.props !== !0 && (l.props = Of.mergeEvaluated.props(t, (0, Of.toHash)(c), l.props));
    const f = c.filter((h) => !(0, Of.alwaysValidSchema)(l, i[h]));
    if (f.length === 0)
      return;
    const d = t.name("valid");
    for (const h of f)
      m(h) ? y(h) : (t.if((0, tv.propertyInData)(t, a, h, l.opts.ownProperties)), y(h), l.allErrors || t.else().var(d, !0), t.endIf()), e.it.definedProperties.add(h), e.ok(d);
    function m(h) {
      return l.opts.useDefaults && !l.compositeRule && i[h].default !== void 0;
    }
    function y(h) {
      e.subschema({
        keyword: "properties",
        schemaProp: h,
        dataProp: h
      }, d);
    }
  }
};
mp.default = h2;
var yp = {};
Object.defineProperty(yp, "__esModule", { value: !0 });
const rv = je, yl = Te, iv = he, ov = he, m2 = {
  keyword: "patternProperties",
  type: "object",
  schemaType: "object",
  code(e) {
    const { gen: t, schema: i, data: o, parentSchema: a, it: l } = e, { opts: c } = l, f = (0, rv.allSchemaProperties)(i), d = f.filter((w) => (0, iv.alwaysValidSchema)(l, i[w]));
    if (f.length === 0 || d.length === f.length && (!l.opts.unevaluated || l.props === !0))
      return;
    const m = c.strictSchema && !c.allowMatchingProperties && a.properties, y = t.name("valid");
    l.props !== !0 && !(l.props instanceof yl.Name) && (l.props = (0, ov.evaluatedPropsToName)(t, l.props));
    const { props: h } = l;
    S();
    function S() {
      for (const w of f)
        m && $(w), l.allErrors ? v(w) : (t.var(y, !0), v(w), t.if(y));
    }
    function $(w) {
      for (const _ in m)
        new RegExp(w).test(_) && (0, iv.checkStrictMode)(l, `property ${_} matches pattern ${w} (use allowMatchingProperties)`);
    }
    function v(w) {
      t.forIn("key", o, (_) => {
        t.if((0, yl._)`${(0, rv.usePattern)(e, w)}.test(${_})`, () => {
          const E = d.includes(w);
          E || e.subschema({
            keyword: "patternProperties",
            schemaProp: w,
            dataProp: _,
            dataPropType: ov.Type.Str
          }, y), l.opts.unevaluated && h !== !0 ? t.assign((0, yl._)`${h}[${_}]`, !0) : !E && !l.allErrors && t.if((0, yl.not)(y), () => t.break());
        });
      });
    }
  }
};
yp.default = m2;
var gp = {};
Object.defineProperty(gp, "__esModule", { value: !0 });
const y2 = he, g2 = {
  keyword: "not",
  schemaType: ["object", "boolean"],
  trackErrors: !0,
  code(e) {
    const { gen: t, schema: i, it: o } = e;
    if ((0, y2.alwaysValidSchema)(o, i)) {
      e.fail();
      return;
    }
    const a = t.name("valid");
    e.subschema({
      keyword: "not",
      compositeRule: !0,
      createErrors: !1,
      allErrors: !1
    }, a), e.failResult(a, () => e.reset(), () => e.error());
  },
  error: { message: "must NOT be valid" }
};
gp.default = g2;
var vp = {};
Object.defineProperty(vp, "__esModule", { value: !0 });
const v2 = je, _2 = {
  keyword: "anyOf",
  schemaType: "array",
  trackErrors: !0,
  code: v2.validateUnion,
  error: { message: "must match a schema in anyOf" }
};
vp.default = _2;
var _p = {};
Object.defineProperty(_p, "__esModule", { value: !0 });
const Nl = Te, S2 = he, w2 = {
  message: "must match exactly one schema in oneOf",
  params: ({ params: e }) => (0, Nl._)`{passingSchemas: ${e.passing}}`
}, E2 = {
  keyword: "oneOf",
  schemaType: "array",
  trackErrors: !0,
  error: w2,
  code(e) {
    const { gen: t, schema: i, parentSchema: o, it: a } = e;
    if (!Array.isArray(i))
      throw new Error("ajv implementation error");
    if (a.opts.discriminator && o.discriminator)
      return;
    const l = i, c = t.let("valid", !1), f = t.let("passing", null), d = t.name("_valid");
    e.setParams({ passing: f }), t.block(m), e.result(c, () => e.reset(), () => e.error(!0));
    function m() {
      l.forEach((y, h) => {
        let S;
        (0, S2.alwaysValidSchema)(a, y) ? t.var(d, !0) : S = e.subschema({
          keyword: "oneOf",
          schemaProp: h,
          compositeRule: !0
        }, d), h > 0 && t.if((0, Nl._)`${d} && ${c}`).assign(c, !1).assign(f, (0, Nl._)`[${f}, ${h}]`).else(), t.if(d, () => {
          t.assign(c, !0), t.assign(f, h), S && e.mergeEvaluated(S, Nl.Name);
        });
      });
    }
  }
};
_p.default = E2;
var Sp = {};
Object.defineProperty(Sp, "__esModule", { value: !0 });
const $2 = he, O2 = {
  keyword: "allOf",
  schemaType: "array",
  code(e) {
    const { gen: t, schema: i, it: o } = e;
    if (!Array.isArray(i))
      throw new Error("ajv implementation error");
    const a = t.name("valid");
    i.forEach((l, c) => {
      if ((0, $2.alwaysValidSchema)(o, l))
        return;
      const f = e.subschema({ keyword: "allOf", schemaProp: c }, a);
      e.ok(a), e.mergeEvaluated(f);
    });
  }
};
Sp.default = O2;
var wp = {};
Object.defineProperty(wp, "__esModule", { value: !0 });
const zl = Te, aS = he, P2 = {
  message: ({ params: e }) => (0, zl.str)`must match "${e.ifClause}" schema`,
  params: ({ params: e }) => (0, zl._)`{failingKeyword: ${e.ifClause}}`
}, C2 = {
  keyword: "if",
  schemaType: ["object", "boolean"],
  trackErrors: !0,
  error: P2,
  code(e) {
    const { gen: t, parentSchema: i, it: o } = e;
    i.then === void 0 && i.else === void 0 && (0, aS.checkStrictMode)(o, '"if" without "then" and "else" is ignored');
    const a = sv(o, "then"), l = sv(o, "else");
    if (!a && !l)
      return;
    const c = t.let("valid", !0), f = t.name("_valid");
    if (d(), e.reset(), a && l) {
      const y = t.let("ifClause");
      e.setParams({ ifClause: y }), t.if(f, m("then", y), m("else", y));
    } else a ? t.if(f, m("then")) : t.if((0, zl.not)(f), m("else"));
    e.pass(c, () => e.error(!0));
    function d() {
      const y = e.subschema({
        keyword: "if",
        compositeRule: !0,
        createErrors: !1,
        allErrors: !1
      }, f);
      e.mergeEvaluated(y);
    }
    function m(y, h) {
      return () => {
        const S = e.subschema({ keyword: y }, f);
        t.assign(c, f), e.mergeValidEvaluated(S, c), h ? t.assign(h, (0, zl._)`${y}`) : e.setParams({ ifClause: y });
      };
    }
  }
};
function sv(e, t) {
  const i = e.schema[t];
  return i !== void 0 && !(0, aS.alwaysValidSchema)(e, i);
}
wp.default = C2;
var Ep = {};
Object.defineProperty(Ep, "__esModule", { value: !0 });
const k2 = he, T2 = {
  keyword: ["then", "else"],
  schemaType: ["object", "boolean"],
  code({ keyword: e, parentSchema: t, it: i }) {
    t.if === void 0 && (0, k2.checkStrictMode)(i, `"${e}" without "if" is ignored`);
  }
};
Ep.default = T2;
Object.defineProperty(cp, "__esModule", { value: !0 });
const N2 = Po, I2 = fp, j2 = Co, A2 = dp, x2 = pp, b2 = oS, F2 = hp, R2 = iu, D2 = mp, M2 = yp, L2 = gp, U2 = vp, z2 = _p, V2 = Sp, B2 = wp, K2 = Ep;
function W2(e = !1) {
  const t = [
    // any
    L2.default,
    U2.default,
    z2.default,
    V2.default,
    B2.default,
    K2.default,
    // object
    F2.default,
    R2.default,
    b2.default,
    D2.default,
    M2.default
  ];
  return e ? t.push(I2.default, A2.default) : t.push(N2.default, j2.default), t.push(x2.default), t;
}
cp.default = W2;
var $p = {}, Op = {};
Object.defineProperty(Op, "__esModule", { value: !0 });
const ut = Te, H2 = {
  message: ({ schemaCode: e }) => (0, ut.str)`must match format "${e}"`,
  params: ({ schemaCode: e }) => (0, ut._)`{format: ${e}}`
}, q2 = {
  keyword: "format",
  type: ["number", "string"],
  schemaType: "string",
  $data: !0,
  error: H2,
  code(e, t) {
    const { gen: i, data: o, $data: a, schema: l, schemaCode: c, it: f } = e, { opts: d, errSchemaPath: m, schemaEnv: y, self: h } = f;
    if (!d.validateFormats)
      return;
    a ? S() : $();
    function S() {
      const v = i.scopeValue("formats", {
        ref: h.formats,
        code: d.code.formats
      }), w = i.const("fDef", (0, ut._)`${v}[${c}]`), _ = i.let("fType"), E = i.let("format");
      i.if((0, ut._)`typeof ${w} == "object" && !(${w} instanceof RegExp)`, () => i.assign(_, (0, ut._)`${w}.type || "string"`).assign(E, (0, ut._)`${w}.validate`), () => i.assign(_, (0, ut._)`"string"`).assign(E, w)), e.fail$data((0, ut.or)(k(), j()));
      function k() {
        return d.strictSchema === !1 ? ut.nil : (0, ut._)`${c} && !${E}`;
      }
      function j() {
        const T = y.$async ? (0, ut._)`(${w}.async ? await ${E}(${o}) : ${E}(${o}))` : (0, ut._)`${E}(${o})`, N = (0, ut._)`(typeof ${E} == "function" ? ${T} : ${E}.test(${o}))`;
        return (0, ut._)`${E} && ${E} !== true && ${_} === ${t} && !${N}`;
      }
    }
    function $() {
      const v = h.formats[l];
      if (!v) {
        k();
        return;
      }
      if (v === !0)
        return;
      const [w, _, E] = j(v);
      w === t && e.pass(T());
      function k() {
        if (d.strictSchema === !1) {
          h.logger.warn(N());
          return;
        }
        throw new Error(N());
        function N() {
          return `unknown format "${l}" ignored in schema at path "${m}"`;
        }
      }
      function j(N) {
        const x = N instanceof RegExp ? (0, ut.regexpCode)(N) : d.code.formats ? (0, ut._)`${d.code.formats}${(0, ut.getProperty)(l)}` : void 0, F = i.scopeValue("formats", { key: l, ref: N, code: x });
        return typeof N == "object" && !(N instanceof RegExp) ? [N.type || "string", N.validate, (0, ut._)`${F}.validate`] : ["string", N, F];
      }
      function T() {
        if (typeof v == "object" && !(v instanceof RegExp) && v.async) {
          if (!y.$async)
            throw new Error("async format in sync schema");
          return (0, ut._)`await ${E}(${o})`;
        }
        return typeof _ == "function" ? (0, ut._)`${E}(${o})` : (0, ut._)`${E}.test(${o})`;
      }
    }
  }
};
Op.default = q2;
Object.defineProperty($p, "__esModule", { value: !0 });
const G2 = Op, Y2 = [G2.default];
$p.default = Y2;
var _o = {};
Object.defineProperty(_o, "__esModule", { value: !0 });
_o.contentVocabulary = _o.metadataVocabulary = void 0;
_o.metadataVocabulary = [
  "title",
  "description",
  "default",
  "deprecated",
  "readOnly",
  "writeOnly",
  "examples"
];
_o.contentVocabulary = [
  "contentMediaType",
  "contentEncoding",
  "contentSchema"
];
Object.defineProperty(Yd, "__esModule", { value: !0 });
const Q2 = Qd, J2 = Xd, X2 = cp, Z2 = $p, av = _o, eF = [
  Q2.default,
  J2.default,
  (0, X2.default)(),
  Z2.default,
  av.metadataVocabulary,
  av.contentVocabulary
];
Yd.default = eF;
var Pp = {}, ou = {};
Object.defineProperty(ou, "__esModule", { value: !0 });
ou.DiscrError = void 0;
var lv;
(function(e) {
  e.Tag = "tag", e.Mapping = "mapping";
})(lv || (ou.DiscrError = lv = {}));
Object.defineProperty(Pp, "__esModule", { value: !0 });
const oo = Te, Yf = ou, uv = Kt, tF = Oo, nF = he, rF = {
  message: ({ params: { discrError: e, tagName: t } }) => e === Yf.DiscrError.Tag ? `tag "${t}" must be string` : `value of tag "${t}" must be in oneOf`,
  params: ({ params: { discrError: e, tag: t, tagName: i } }) => (0, oo._)`{error: ${e}, tag: ${i}, tagValue: ${t}}`
}, iF = {
  keyword: "discriminator",
  type: "object",
  schemaType: "object",
  error: rF,
  code(e) {
    const { gen: t, data: i, schema: o, parentSchema: a, it: l } = e, { oneOf: c } = a;
    if (!l.opts.discriminator)
      throw new Error("discriminator: requires discriminator option");
    const f = o.propertyName;
    if (typeof f != "string")
      throw new Error("discriminator: requires propertyName");
    if (o.mapping)
      throw new Error("discriminator: mapping is not supported");
    if (!c)
      throw new Error("discriminator: requires oneOf keyword");
    const d = t.let("valid", !1), m = t.const("tag", (0, oo._)`${i}${(0, oo.getProperty)(f)}`);
    t.if((0, oo._)`typeof ${m} == "string"`, () => y(), () => e.error(!1, { discrError: Yf.DiscrError.Tag, tag: m, tagName: f })), e.ok(d);
    function y() {
      const $ = S();
      t.if(!1);
      for (const v in $)
        t.elseIf((0, oo._)`${m} === ${v}`), t.assign(d, h($[v]));
      t.else(), e.error(!1, { discrError: Yf.DiscrError.Mapping, tag: m, tagName: f }), t.endIf();
    }
    function h($) {
      const v = t.name("valid"), w = e.subschema({ keyword: "oneOf", schemaProp: $ }, v);
      return e.mergeEvaluated(w, oo.Name), v;
    }
    function S() {
      var $;
      const v = {}, w = E(a);
      let _ = !0;
      for (let T = 0; T < c.length; T++) {
        let N = c[T];
        if (N != null && N.$ref && !(0, nF.schemaHasRulesButRef)(N, l.self.RULES)) {
          const F = N.$ref;
          if (N = uv.resolveRef.call(l.self, l.schemaEnv.root, l.baseId, F), N instanceof uv.SchemaEnv && (N = N.schema), N === void 0)
            throw new tF.default(l.opts.uriResolver, l.baseId, F);
        }
        const x = ($ = N == null ? void 0 : N.properties) === null || $ === void 0 ? void 0 : $[f];
        if (typeof x != "object")
          throw new Error(`discriminator: oneOf subschemas (or referenced schemas) must have "properties/${f}"`);
        _ = _ && (w || E(N)), k(x, T);
      }
      if (!_)
        throw new Error(`discriminator: "${f}" must be required`);
      return v;
      function E({ required: T }) {
        return Array.isArray(T) && T.includes(f);
      }
      function k(T, N) {
        if (T.const)
          j(T.const, N);
        else if (T.enum)
          for (const x of T.enum)
            j(x, N);
        else
          throw new Error(`discriminator: "properties/${f}" must have "const" or "enum"`);
      }
      function j(T, N) {
        if (typeof T != "string" || T in v)
          throw new Error(`discriminator: "${f}" values must be unique strings`);
        v[T] = N;
      }
    }
  }
};
Pp.default = iF;
const oF = "http://json-schema.org/draft-07/schema#", sF = "http://json-schema.org/draft-07/schema#", aF = "Core schema meta-schema", lF = {
  schemaArray: {
    type: "array",
    minItems: 1,
    items: {
      $ref: "#"
    }
  },
  nonNegativeInteger: {
    type: "integer",
    minimum: 0
  },
  nonNegativeIntegerDefault0: {
    allOf: [
      {
        $ref: "#/definitions/nonNegativeInteger"
      },
      {
        default: 0
      }
    ]
  },
  simpleTypes: {
    enum: [
      "array",
      "boolean",
      "integer",
      "null",
      "number",
      "object",
      "string"
    ]
  },
  stringArray: {
    type: "array",
    items: {
      type: "string"
    },
    uniqueItems: !0,
    default: []
  }
}, uF = [
  "object",
  "boolean"
], cF = {
  $id: {
    type: "string",
    format: "uri-reference"
  },
  $schema: {
    type: "string",
    format: "uri"
  },
  $ref: {
    type: "string",
    format: "uri-reference"
  },
  $comment: {
    type: "string"
  },
  title: {
    type: "string"
  },
  description: {
    type: "string"
  },
  default: !0,
  readOnly: {
    type: "boolean",
    default: !1
  },
  examples: {
    type: "array",
    items: !0
  },
  multipleOf: {
    type: "number",
    exclusiveMinimum: 0
  },
  maximum: {
    type: "number"
  },
  exclusiveMaximum: {
    type: "number"
  },
  minimum: {
    type: "number"
  },
  exclusiveMinimum: {
    type: "number"
  },
  maxLength: {
    $ref: "#/definitions/nonNegativeInteger"
  },
  minLength: {
    $ref: "#/definitions/nonNegativeIntegerDefault0"
  },
  pattern: {
    type: "string",
    format: "regex"
  },
  additionalItems: {
    $ref: "#"
  },
  items: {
    anyOf: [
      {
        $ref: "#"
      },
      {
        $ref: "#/definitions/schemaArray"
      }
    ],
    default: !0
  },
  maxItems: {
    $ref: "#/definitions/nonNegativeInteger"
  },
  minItems: {
    $ref: "#/definitions/nonNegativeIntegerDefault0"
  },
  uniqueItems: {
    type: "boolean",
    default: !1
  },
  contains: {
    $ref: "#"
  },
  maxProperties: {
    $ref: "#/definitions/nonNegativeInteger"
  },
  minProperties: {
    $ref: "#/definitions/nonNegativeIntegerDefault0"
  },
  required: {
    $ref: "#/definitions/stringArray"
  },
  additionalProperties: {
    $ref: "#"
  },
  definitions: {
    type: "object",
    additionalProperties: {
      $ref: "#"
    },
    default: {}
  },
  properties: {
    type: "object",
    additionalProperties: {
      $ref: "#"
    },
    default: {}
  },
  patternProperties: {
    type: "object",
    additionalProperties: {
      $ref: "#"
    },
    propertyNames: {
      format: "regex"
    },
    default: {}
  },
  dependencies: {
    type: "object",
    additionalProperties: {
      anyOf: [
        {
          $ref: "#"
        },
        {
          $ref: "#/definitions/stringArray"
        }
      ]
    }
  },
  propertyNames: {
    $ref: "#"
  },
  const: !0,
  enum: {
    type: "array",
    items: !0,
    minItems: 1,
    uniqueItems: !0
  },
  type: {
    anyOf: [
      {
        $ref: "#/definitions/simpleTypes"
      },
      {
        type: "array",
        items: {
          $ref: "#/definitions/simpleTypes"
        },
        minItems: 1,
        uniqueItems: !0
      }
    ]
  },
  format: {
    type: "string"
  },
  contentMediaType: {
    type: "string"
  },
  contentEncoding: {
    type: "string"
  },
  if: {
    $ref: "#"
  },
  then: {
    $ref: "#"
  },
  else: {
    $ref: "#"
  },
  allOf: {
    $ref: "#/definitions/schemaArray"
  },
  anyOf: {
    $ref: "#/definitions/schemaArray"
  },
  oneOf: {
    $ref: "#/definitions/schemaArray"
  },
  not: {
    $ref: "#"
  }
}, fF = {
  $schema: oF,
  $id: sF,
  title: aF,
  definitions: lF,
  type: uF,
  properties: cF,
  default: !0
};
(function(e, t) {
  Object.defineProperty(t, "__esModule", { value: !0 }), t.MissingRefError = t.ValidationError = t.CodeGen = t.Name = t.nil = t.stringify = t.str = t._ = t.KeywordCxt = t.Ajv = void 0;
  const i = S_, o = Yd, a = Pp, l = fF, c = ["/properties"], f = "http://json-schema.org/draft-07/schema";
  class d extends i.default {
    _addVocabularies() {
      super._addVocabularies(), o.default.forEach((v) => this.addVocabulary(v)), this.opts.discriminator && this.addKeyword(a.default);
    }
    _addDefaultMetaSchema() {
      if (super._addDefaultMetaSchema(), !this.opts.meta)
        return;
      const v = this.opts.$data ? this.$dataMetaSchema(l, c) : l;
      this.addMetaSchema(v, f, !1), this.refs["http://json-schema.org/schema"] = f;
    }
    defaultMeta() {
      return this.opts.defaultMeta = super.defaultMeta() || (this.getSchema(f) ? f : void 0);
    }
  }
  t.Ajv = d, e.exports = t = d, e.exports.Ajv = d, Object.defineProperty(t, "__esModule", { value: !0 }), t.default = d;
  var m = wn;
  Object.defineProperty(t, "KeywordCxt", { enumerable: !0, get: function() {
    return m.KeywordCxt;
  } });
  var y = Te;
  Object.defineProperty(t, "_", { enumerable: !0, get: function() {
    return y._;
  } }), Object.defineProperty(t, "str", { enumerable: !0, get: function() {
    return y.str;
  } }), Object.defineProperty(t, "stringify", { enumerable: !0, get: function() {
    return y.stringify;
  } }), Object.defineProperty(t, "nil", { enumerable: !0, get: function() {
    return y.nil;
  } }), Object.defineProperty(t, "Name", { enumerable: !0, get: function() {
    return y.Name;
  } }), Object.defineProperty(t, "CodeGen", { enumerable: !0, get: function() {
    return y.CodeGen;
  } });
  var h = Hd();
  Object.defineProperty(t, "ValidationError", { enumerable: !0, get: function() {
    return h.default;
  } });
  var S = Oo;
  Object.defineProperty(t, "MissingRefError", { enumerable: !0, get: function() {
    return S.default;
  } });
})(Vf, Vf.exports);
var lS = Vf.exports;
const dF = /* @__PURE__ */ zs(lS);
var Qf = { exports: {} }, uS = {};
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.formatNames = e.fastFormats = e.fullFormats = void 0;
  function t(U, G) {
    return { validate: U, compare: G };
  }
  e.fullFormats = {
    // date: http://tools.ietf.org/html/rfc3339#section-5.6
    date: t(l, c),
    // date-time: http://tools.ietf.org/html/rfc3339#section-5.6
    time: t(d, m),
    "date-time": t(h, S),
    // duration: https://tools.ietf.org/html/rfc3339#appendix-A
    duration: /^P(?!$)((\d+Y)?(\d+M)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?|(\d+W)?)$/,
    uri: w,
    "uri-reference": /^(?:[a-z][a-z0-9+\-.]*:)?(?:\/?\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:]|%[0-9a-f]{2})*@)?(?:\[(?:(?:(?:(?:[0-9a-f]{1,4}:){6}|::(?:[0-9a-f]{1,4}:){5}|(?:[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){4}|(?:(?:[0-9a-f]{1,4}:){0,1}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){3}|(?:(?:[0-9a-f]{1,4}:){0,2}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){2}|(?:(?:[0-9a-f]{1,4}:){0,3}[0-9a-f]{1,4})?::[0-9a-f]{1,4}:|(?:(?:[0-9a-f]{1,4}:){0,4}[0-9a-f]{1,4})?::)(?:[0-9a-f]{1,4}:[0-9a-f]{1,4}|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|(?:(?:[0-9a-f]{1,4}:){0,5}[0-9a-f]{1,4})?::[0-9a-f]{1,4}|(?:(?:[0-9a-f]{1,4}:){0,6}[0-9a-f]{1,4})?::)|[Vv][0-9a-f]+\.[a-z0-9\-._~!$&'()*+,;=:]+)\]|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)|(?:[a-z0-9\-._~!$&'"()*+,;=]|%[0-9a-f]{2})*)(?::\d*)?(?:\/(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})*)*|\/(?:(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})*)*)?|(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'"()*+,;=:@]|%[0-9a-f]{2})*)*)?(?:\?(?:[a-z0-9\-._~!$&'"()*+,;=:@/?]|%[0-9a-f]{2})*)?(?:#(?:[a-z0-9\-._~!$&'"()*+,;=:@/?]|%[0-9a-f]{2})*)?$/i,
    // uri-template: https://tools.ietf.org/html/rfc6570
    "uri-template": /^(?:(?:[^\x00-\x20"'<>%\\^`{|}]|%[0-9a-f]{2})|\{[+#./;?&=,!@|]?(?:[a-z0-9_]|%[0-9a-f]{2})+(?::[1-9][0-9]{0,3}|\*)?(?:,(?:[a-z0-9_]|%[0-9a-f]{2})+(?::[1-9][0-9]{0,3}|\*)?)*\})*$/i,
    // For the source: https://gist.github.com/dperini/729294
    // For test cases: https://mathiasbynens.be/demo/url-regex
    url: /^(?:https?|ftp):\/\/(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z0-9\u{00a1}-\u{ffff}]+-)*[a-z0-9\u{00a1}-\u{ffff}]+)(?:\.(?:[a-z0-9\u{00a1}-\u{ffff}]+-)*[a-z0-9\u{00a1}-\u{ffff}]+)*(?:\.(?:[a-z\u{00a1}-\u{ffff}]{2,})))(?::\d{2,5})?(?:\/[^\s]*)?$/iu,
    email: /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i,
    hostname: /^(?=.{1,253}\.?$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[-0-9a-z]{0,61}[0-9a-z])?)*\.?$/i,
    // optimized https://www.safaribooksonline.com/library/view/regular-expressions-cookbook/9780596802837/ch07s16.html
    ipv4: /^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$/,
    ipv6: /^((([0-9a-f]{1,4}:){7}([0-9a-f]{1,4}|:))|(([0-9a-f]{1,4}:){6}(:[0-9a-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9a-f]{1,4}:){5}(((:[0-9a-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9a-f]{1,4}:){4}(((:[0-9a-f]{1,4}){1,3})|((:[0-9a-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9a-f]{1,4}:){3}(((:[0-9a-f]{1,4}){1,4})|((:[0-9a-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9a-f]{1,4}:){2}(((:[0-9a-f]{1,4}){1,5})|((:[0-9a-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9a-f]{1,4}:){1}(((:[0-9a-f]{1,4}){1,6})|((:[0-9a-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9a-f]{1,4}){1,7})|((:[0-9a-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))$/i,
    regex: V,
    // uuid: http://tools.ietf.org/html/rfc4122
    uuid: /^(?:urn:uuid:)?[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i,
    // JSON-pointer: https://tools.ietf.org/html/rfc6901
    // uri fragment: https://tools.ietf.org/html/rfc3986#appendix-A
    "json-pointer": /^(?:\/(?:[^~/]|~0|~1)*)*$/,
    "json-pointer-uri-fragment": /^#(?:\/(?:[a-z0-9_\-.!$&'()*+,;:=@]|%[0-9a-f]{2}|~0|~1)*)*$/i,
    // relative JSON-pointer: http://tools.ietf.org/html/draft-luff-relative-json-pointer-00
    "relative-json-pointer": /^(?:0|[1-9][0-9]*)(?:#|(?:\/(?:[^~/]|~0|~1)*)*)$/,
    // the following formats are used by the openapi specification: https://spec.openapis.org/oas/v3.0.0#data-types
    // byte: https://github.com/miguelmota/is-base64
    byte: E,
    // signed 32 bit integer
    int32: { type: "number", validate: T },
    // signed 64 bit integer
    int64: { type: "number", validate: N },
    // C-type float
    float: { type: "number", validate: x },
    // C-type double
    double: { type: "number", validate: x },
    // hint to the UI to hide input strings
    password: !0,
    // unchecked string payload
    binary: !0
  }, e.fastFormats = {
    ...e.fullFormats,
    date: t(/^\d\d\d\d-[0-1]\d-[0-3]\d$/, c),
    time: t(/^(?:[0-2]\d:[0-5]\d:[0-5]\d|23:59:60)(?:\.\d+)?(?:z|[+-]\d\d(?::?\d\d)?)?$/i, m),
    "date-time": t(/^\d\d\d\d-[0-1]\d-[0-3]\d[t\s](?:[0-2]\d:[0-5]\d:[0-5]\d|23:59:60)(?:\.\d+)?(?:z|[+-]\d\d(?::?\d\d)?)$/i, S),
    // uri: https://github.com/mafintosh/is-my-json-valid/blob/master/formats.js
    uri: /^(?:[a-z][a-z0-9+\-.]*:)(?:\/?\/)?[^\s]*$/i,
    "uri-reference": /^(?:(?:[a-z][a-z0-9+\-.]*:)?\/?\/)?(?:[^\\\s#][^\s#]*)?(?:#[^\\\s]*)?$/i,
    // email (sources from jsen validator):
    // http://stackoverflow.com/questions/201323/using-a-regular-expression-to-validate-an-email-address#answer-8829363
    // http://www.w3.org/TR/html5/forms.html#valid-e-mail-address (search for 'wilful violation')
    email: /^[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*$/i
  }, e.formatNames = Object.keys(e.fullFormats);
  function i(U) {
    return U % 4 === 0 && (U % 100 !== 0 || U % 400 === 0);
  }
  const o = /^(\d\d\d\d)-(\d\d)-(\d\d)$/, a = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  function l(U) {
    const G = o.exec(U);
    if (!G)
      return !1;
    const Q = +G[1], H = +G[2], q = +G[3];
    return H >= 1 && H <= 12 && q >= 1 && q <= (H === 2 && i(Q) ? 29 : a[H]);
  }
  function c(U, G) {
    if (U && G)
      return U > G ? 1 : U < G ? -1 : 0;
  }
  const f = /^(\d\d):(\d\d):(\d\d)(\.\d+)?(z|[+-]\d\d(?::?\d\d)?)?$/i;
  function d(U, G) {
    const Q = f.exec(U);
    if (!Q)
      return !1;
    const H = +Q[1], q = +Q[2], le = +Q[3], ie = Q[5];
    return (H <= 23 && q <= 59 && le <= 59 || H === 23 && q === 59 && le === 60) && (!G || ie !== "");
  }
  function m(U, G) {
    if (!(U && G))
      return;
    const Q = f.exec(U), H = f.exec(G);
    if (Q && H)
      return U = Q[1] + Q[2] + Q[3] + (Q[4] || ""), G = H[1] + H[2] + H[3] + (H[4] || ""), U > G ? 1 : U < G ? -1 : 0;
  }
  const y = /t|\s/i;
  function h(U) {
    const G = U.split(y);
    return G.length === 2 && l(G[0]) && d(G[1], !0);
  }
  function S(U, G) {
    if (!(U && G))
      return;
    const [Q, H] = U.split(y), [q, le] = G.split(y), ie = c(Q, q);
    if (ie !== void 0)
      return ie || m(H, le);
  }
  const $ = /\/|:/, v = /^(?:[a-z][a-z0-9+\-.]*:)(?:\/?\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:]|%[0-9a-f]{2})*@)?(?:\[(?:(?:(?:(?:[0-9a-f]{1,4}:){6}|::(?:[0-9a-f]{1,4}:){5}|(?:[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){4}|(?:(?:[0-9a-f]{1,4}:){0,1}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){3}|(?:(?:[0-9a-f]{1,4}:){0,2}[0-9a-f]{1,4})?::(?:[0-9a-f]{1,4}:){2}|(?:(?:[0-9a-f]{1,4}:){0,3}[0-9a-f]{1,4})?::[0-9a-f]{1,4}:|(?:(?:[0-9a-f]{1,4}:){0,4}[0-9a-f]{1,4})?::)(?:[0-9a-f]{1,4}:[0-9a-f]{1,4}|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?))|(?:(?:[0-9a-f]{1,4}:){0,5}[0-9a-f]{1,4})?::[0-9a-f]{1,4}|(?:(?:[0-9a-f]{1,4}:){0,6}[0-9a-f]{1,4})?::)|[Vv][0-9a-f]+\.[a-z0-9\-._~!$&'()*+,;=:]+)\]|(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)|(?:[a-z0-9\-._~!$&'()*+,;=]|%[0-9a-f]{2})*)(?::\d*)?(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})*)*|\/(?:(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})*)*)?|(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})+(?:\/(?:[a-z0-9\-._~!$&'()*+,;=:@]|%[0-9a-f]{2})*)*)(?:\?(?:[a-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9a-f]{2})*)?(?:#(?:[a-z0-9\-._~!$&'()*+,;=:@/?]|%[0-9a-f]{2})*)?$/i;
  function w(U) {
    return $.test(U) && v.test(U);
  }
  const _ = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/gm;
  function E(U) {
    return _.lastIndex = 0, _.test(U);
  }
  const k = -2147483648, j = 2 ** 31 - 1;
  function T(U) {
    return Number.isInteger(U) && U <= j && U >= k;
  }
  function N(U) {
    return Number.isInteger(U);
  }
  function x() {
    return !0;
  }
  const F = /[^\\]\\Z/;
  function V(U) {
    if (F.test(U))
      return !1;
    try {
      return new RegExp(U), !0;
    } catch {
      return !1;
    }
  }
})(uS);
var cS = {};
(function(e) {
  Object.defineProperty(e, "__esModule", { value: !0 }), e.formatLimitDefinition = void 0;
  const t = lS, i = Te, o = i.operators, a = {
    formatMaximum: { okStr: "<=", ok: o.LTE, fail: o.GT },
    formatMinimum: { okStr: ">=", ok: o.GTE, fail: o.LT },
    formatExclusiveMaximum: { okStr: "<", ok: o.LT, fail: o.GTE },
    formatExclusiveMinimum: { okStr: ">", ok: o.GT, fail: o.LTE }
  }, l = {
    message: ({ keyword: f, schemaCode: d }) => i.str`should be ${a[f].okStr} ${d}`,
    params: ({ keyword: f, schemaCode: d }) => i._`{comparison: ${a[f].okStr}, limit: ${d}}`
  };
  e.formatLimitDefinition = {
    keyword: Object.keys(a),
    type: "string",
    schemaType: "string",
    $data: !0,
    error: l,
    code(f) {
      const { gen: d, data: m, schemaCode: y, keyword: h, it: S } = f, { opts: $, self: v } = S;
      if (!$.validateFormats)
        return;
      const w = new t.KeywordCxt(S, v.RULES.all.format.definition, "format");
      w.$data ? _() : E();
      function _() {
        const j = d.scopeValue("formats", {
          ref: v.formats,
          code: $.code.formats
        }), T = d.const("fmt", i._`${j}[${w.schemaCode}]`);
        f.fail$data(i.or(i._`typeof ${T} != "object"`, i._`${T} instanceof RegExp`, i._`typeof ${T}.compare != "function"`, k(T)));
      }
      function E() {
        const j = w.schema, T = v.formats[j];
        if (!T || T === !0)
          return;
        if (typeof T != "object" || T instanceof RegExp || typeof T.compare != "function")
          throw new Error(`"${h}": format "${j}" does not define "compare" function`);
        const N = d.scopeValue("formats", {
          key: j,
          ref: T,
          code: $.code.formats ? i._`${$.code.formats}${i.getProperty(j)}` : void 0
        });
        f.fail$data(k(N));
      }
      function k(j) {
        return i._`${j}.compare(${m}, ${y}) ${a[h].fail} 0`;
      }
    },
    dependencies: ["format"]
  };
  const c = (f) => (f.addKeyword(e.formatLimitDefinition), f);
  e.default = c;
})(cS);
(function(e, t) {
  Object.defineProperty(t, "__esModule", { value: !0 });
  const i = uS, o = cS, a = Te, l = new a.Name("fullFormats"), c = new a.Name("fastFormats"), f = (m, y = { keywords: !0 }) => {
    if (Array.isArray(y))
      return d(m, y, i.fullFormats, l), m;
    const [h, S] = y.mode === "fast" ? [i.fastFormats, c] : [i.fullFormats, l], $ = y.formats || i.formatNames;
    return d(m, $, h, S), y.keywords && o.default(m), m;
  };
  f.get = (m, y = "full") => {
    const S = (y === "fast" ? i.fastFormats : i.fullFormats)[m];
    if (!S)
      throw new Error(`Unknown format "${m}"`);
    return S;
  };
  function d(m, y, h, S) {
    var $, v;
    ($ = (v = m.opts.code).formats) !== null && $ !== void 0 || (v.formats = a._`require("ajv-formats/dist/formats").${S}`);
    for (const w of y)
      m.addFormat(w, h[w]);
  }
  e.exports = t = f, Object.defineProperty(t, "__esModule", { value: !0 }), t.default = f;
})(Qf, Qf.exports);
var pF = Qf.exports;
const cv = /* @__PURE__ */ zs(pF), hF = {
  allErrors: !0,
  multipleOfPrecision: 8,
  strict: !1,
  verbose: !0,
  discriminator: !1
  // TODO enable this in V6
}, mF = /^(#?([0-9A-Fa-f]{3}){1,2}\b|aqua|black|blue|fuchsia|gray|green|lime|maroon|navy|olive|orange|purple|red|silver|teal|white|yellow|(rgb\(\s*\b([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\b\s*,\s*\b([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\b\s*,\s*\b([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\b\s*\))|(rgb\(\s*(\d?\d%|100%)+\s*,\s*(\d?\d%|100%)+\s*,\s*(\d?\d%|100%)+\s*\)))$/, yF = /^data:([a-z]+\/[a-z0-9-+.]+)?;(?:name=(.*);)?base64,(.*)$/;
function gF(e, t, i = {}, o, a = dF, l) {
  let c = new a({ ...hF, ...i });
  return o ? cv(c, o) : o !== !1 && cv(c), c.addFormat("data-url", yF), c.addFormat("color", mF), c.addKeyword(Fr), c.addKeyword(Xf), Array.isArray(e) && c.addMetaSchema(e), Fe(t) && Object.keys(t).forEach((f) => {
    c.addFormat(f, t[f]);
  }), l && (c = l(c)), c;
}
function vF(e = [], t) {
  return e.map((o) => {
    var a;
    const { instancePath: l, keyword: c, params: f, schemaPath: d, parentSchema: m, ...y } = o;
    let { message: h = "" } = y, S = l.replace(/\//g, "."), $ = `${S} ${h}`.trim(), v = "";
    const w = [
      ...((a = f.deps) === null || a === void 0 ? void 0 : a.split(", ")) || [],
      f.missingProperty,
      f.property
    ].filter((_) => _);
    if (w.length > 0)
      w.forEach((_) => {
        const E = S ? `${S}.${_}` : _;
        let k = Ee(re(t, `${E.replace(/^\./, "")}`)).title;
        if (k === void 0) {
          const j = d.replace(/\/properties\//g, "/").split("/").slice(1, -1).concat([_]);
          k = Ee(re(t, j)).title;
        }
        if (k)
          h = h.replace(`'${_}'`, `'${k}'`), v = k;
        else {
          const j = re(m, [Me, _, "title"]);
          j && (h = h.replace(`'${_}'`, `'${j}'`), v = j);
        }
      }), $ = h;
    else {
      const _ = Ee(re(t, `${S.replace(/^\./, "")}`)).title;
      if (_)
        $ = `'${_}' ${h}`.trim(), v = _;
      else {
        const E = m == null ? void 0 : m.title;
        E && ($ = `'${E}' ${h}`.trim(), v = E);
      }
    }
    return "missingProperty" in f && (S = S ? `${S}.${f.missingProperty}` : f.missingProperty), {
      name: c,
      property: S,
      message: h,
      params: f,
      // specific to ajv
      stack: $,
      schemaPath: d,
      title: v
    };
  }).reduce((o, a) => {
    const { message: l, schemaPath: c } = a, f = c == null ? void 0 : c.indexOf(`/${be}/`), d = c == null ? void 0 : c.indexOf(`/${Ne}/`);
    let m;
    return f && f >= 0 ? m = c == null ? void 0 : c.substring(0, f) : d && d >= 0 && (m = c == null ? void 0 : c.substring(0, d)), (m ? o.find((h) => {
      var S;
      return h.message === l && ((S = h.schemaPath) === null || S === void 0 ? void 0 : S.startsWith(m));
    }) : void 0) || o.push(a), o;
  }, []);
}
function _F(e, t, i, o, a, l, c) {
  const { validationError: f } = t;
  let d = vF(t.errors, c);
  f && (d = [...d, { stack: f.message }]), typeof l == "function" && (d = l(d, c));
  let m = BT(d);
  if (f && (m = {
    ...m,
    $schema: {
      __errors: [f.message]
    }
  }), typeof a != "function")
    return { errors: d, errorSchema: m };
  const y = L0(e, o, i, o, !0), h = a(y, kf(y), c), S = X0(h);
  return Ol({ errors: d, errorSchema: m }, S);
}
class SF {
  /** Constructs an `AJV8Validator` instance using the `options`
   *
   * @param options - The `CustomValidatorOptionsType` options that are used to create the AJV instance
   * @param [localizer] - If provided, is used to localize a list of Ajv `ErrorObject`s
   */
  constructor(t, i) {
    const { additionalMetaSchemas: o, customFormats: a, ajvOptionsOverrides: l, ajvFormatOptions: c, AjvClass: f, extenderFn: d } = t;
    this.ajv = gF(o, a, l, c, f, d), this.localizer = i;
  }
  /** Resets the internal AJV validator to clear schemas from it. Can be helpful for resetting the validator for tests.
   */
  reset() {
    this.ajv.removeSchema();
  }
  /** Runs the pure validation of the `schema` and `formData` without any of the RJSF functionality. Provided for use
   * by the playground. Returns the `errors` from the validation
   *
   * @param schema - The schema against which to validate the form data   * @param schema
   * @param formData - The form data to validate
   */
  rawValidation(t, i) {
    var o, a;
    let l, c;
    try {
      t[Ke] && (c = this.ajv.getSchema(t[Ke])), c === void 0 && (c = this.ajv.compile(t)), c(i);
    } catch (d) {
      l = d;
    }
    let f;
    return c && (typeof this.localizer == "function" && (((o = c.errors) !== null && o !== void 0 ? o : []).forEach((d) => {
      var m;
      ["missingProperty", "property"].forEach((y) => {
        var h;
        !((h = d.params) === null || h === void 0) && h[y] && (d.params[y] = `'${d.params[y]}'`);
      }), !((m = d.params) === null || m === void 0) && m.deps && (d.params.deps = d.params.deps.split(", ").map((y) => `'${y}'`).join(", "));
    }), this.localizer(c.errors), ((a = c.errors) !== null && a !== void 0 ? a : []).forEach((d) => {
      var m;
      ["missingProperty", "property"].forEach((y) => {
        var h;
        !((h = d.params) === null || h === void 0) && h[y] && (d.params[y] = d.params[y].slice(1, -1));
      }), !((m = d.params) === null || m === void 0) && m.deps && (d.params.deps = d.params.deps.split(", ").map((y) => y.slice(1, -1)).join(", "));
    })), f = c.errors || void 0, c.errors = null), {
      errors: f,
      validationError: l
    };
  }
  /** This function processes the `formData` with an optional user contributed `customValidate` function, which receives
   * the form data and a `errorHandler` function that will be used to add custom validation errors for each field. Also
   * supports a `transformErrors` function that will take the raw AJV validation errors, prior to custom validation and
   * transform them in what ever way it chooses.
   *
   * @param formData - The form data to validate
   * @param schema - The schema against which to validate the form data
   * @param [customValidate] - An optional function that is used to perform custom validation
   * @param [transformErrors] - An optional function that is used to transform errors after AJV validation
   * @param [uiSchema] - An optional uiSchema that is passed to `transformErrors` and `customValidate`
   */
  validateFormData(t, i, o, a, l) {
    const c = this.rawValidation(i, t);
    return _F(this, c, t, i, o, a, l);
  }
  /**
   * This function checks if a schema needs to be added and if the root schemas don't match it removes the old root schema from the ajv instance and adds the new one.
   * @param rootSchema - The root schema used to provide $ref resolutions
   */
  handleSchemaUpdate(t) {
    var i, o;
    const a = (i = t[Ke]) !== null && i !== void 0 ? i : _v;
    this.ajv.getSchema(a) === void 0 ? this.ajv.addSchema(t, a) : Ge(t, (o = this.ajv.getSchema(a)) === null || o === void 0 ? void 0 : o.schema) || (this.ajv.removeSchema(a), this.ajv.addSchema(t, a));
  }
  /** Validates data against a schema, returning true if the data is valid, or
   * false otherwise. If the schema is invalid, then this function will return
   * false.
   *
   * @param schema - The schema against which to validate the form data
   * @param formData - The form data to validate
   * @param rootSchema - The root schema used to provide $ref resolutions
   */
  isValid(t, i, o) {
    var a;
    try {
      this.handleSchemaUpdate(o);
      const l = Ad(t), c = (a = l[Ke]) !== null && a !== void 0 ? a : DT(l);
      let f;
      return f = this.ajv.getSchema(c), f === void 0 && (f = this.ajv.addSchema(l, c).getSchema(c) || this.ajv.compile(l)), f(i);
    } catch (l) {
      return console.warn("Error encountered compiling schema:", l), !1;
    }
  }
}
function wF(e = {}, t) {
  return new SF(e, t);
}
const EF = wF(), $F = console.error, OF = console.warn;
console.error = (...e) => {
  e.some((t) => typeof t == "string" && t.includes("defaultProps")) || $F.apply(console, e);
};
console.warn = (...e) => {
  e.some((t) => typeof t == "string" && t.includes("defaultProps")) || OF.apply(console, e);
};
class PF extends HTMLElement {
  constructor() {
    super(), this.attachShadow({ mode: "open" }), this._schema = {}, this._uiSchema = {}, this._formData = {}, this._reactRoot = null, this._container = null;
  }
  static get observedAttributes() {
    return ["schema", "ui-schema", "form-data"];
  }
  connectedCallback() {
    this._container = document.createElement("div"), this._container.style.width = "100%", this.shadowRoot.appendChild(this._container), this._reactRoot = hv(this._container), this.render();
  }
  disconnectedCallback() {
    this._reactRoot && (this._reactRoot.unmount(), this._reactRoot = null);
  }
  attributeChangedCallback(t, i, o) {
    if (i !== o)
      try {
        t === "schema" ? this._schema = o ? JSON.parse(o) : {} : t === "ui-schema" ? this._uiSchema = o ? JSON.parse(o) : {} : t === "form-data" && (this._formData = o ? JSON.parse(o) : {}), this.render();
      } catch (a) {
        console.error(`Error parsing ${t}:`, a);
      }
  }
  // Public API: Set schema programmatically
  setSchema(t) {
    this._schema = t, this.setAttribute("schema", JSON.stringify(t));
  }
  // Public API: Set UI schema programmatically
  setUISchema(t) {
    this._uiSchema = t, this.setAttribute("ui-schema", JSON.stringify(t));
  }
  // Public API: Set form data programmatically
  setFormData(t) {
    this._formData = t, this.setAttribute("form-data", JSON.stringify(t));
  }
  // Public API: Get current form data
  getFormData() {
    return this._formData;
  }
  render() {
    if (!this._reactRoot || !this._container)
      return;
    const t = ({ formData: a }) => {
      this._formData = a, this.dispatchEvent(new CustomEvent("change", {
        detail: {
          formData: a,
          valid: !0
          // Could validate here if needed
        },
        bubbles: !0,
        composed: !0
      }));
    }, i = ({ formData: a }) => {
      this._formData = a, this.dispatchEvent(new CustomEvent("submit", {
        detail: {
          formData: a
        },
        bubbles: !0,
        composed: !0
      }));
    }, o = (a) => {
      this.dispatchEvent(new CustomEvent("error", {
        detail: {
          errors: a
        },
        bubbles: !0,
        composed: !0
      }));
    };
    this._reactRoot.render(
      Gc.createElement("div", {
        style: {
          width: "100%",
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          padding: "16px"
        }
      }, [
        Gc.createElement("style", { key: "styles" }, `
          :host {
            display: block;
            width: 100%;
          }
          .rjsf {
            background: #ffffff;
            border-radius: 8px;
          }
          .rjsf .form-group {
            margin-bottom: 24px;
          }
          .rjsf .form-group > label,
          .rjsf .control-label {
            font-weight: 600;
            font-size: 14px;
            color: #4313C8;
            margin-bottom: 8px;
            display: block;
          }
          .rjsf input[type="text"],
          .rjsf input[type="email"],
          .rjsf input[type="url"],
          .rjsf input[type="date"],
          .rjsf input[type="number"],
          .rjsf select,
          .rjsf textarea {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #c0c4fa;
            border-radius: 6px;
            font-size: 14px;
            background-color: #ffffff;
            box-sizing: border-box;
          }
          .rjsf input:focus,
          .rjsf select:focus,
          .rjsf textarea:focus {
            outline: none;
            border-color: #4313C8;
            box-shadow: 0 0 0 2px rgba(67, 19, 200, 0.1);
          }
          .rjsf .btn {
            background: #4313C8;
            color: white;
            border: none;
            padding: 12px 32px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 16px;
          }
          .rjsf .btn:hover {
            background: #979DF6;
          }
        `),
        Gc.createElement(nA, {
          key: "form",
          schema: this._schema,
          uiSchema: this._uiSchema,
          formData: this._formData,
          validator: EF,
          onChange: t,
          onSubmit: i,
          onError: o,
          showErrorList: !1
        })
      ])
    );
  }
}
customElements.get("json-schema-form") || customElements.define("json-schema-form", PF);
export {
  PF as default
};
