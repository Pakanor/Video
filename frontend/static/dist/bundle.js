/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./src/index.ts":
/*!**********************!*\
  !*** ./src/index.ts ***!
  \**********************/
/***/ (() => {

eval("\nfunction sendVideoProgress(currentTime) {\n    fetch('save-video-progress/', {\n        method: 'POST',\n        headers: {\n            'Content-Type': 'application/json', // Ustawienie nagłówka\n        },\n        body: JSON.stringify({\n            currentTime: currentTime, // Przekazanie danych w JSON\n        }),\n    })\n        .then(function (response) {\n        if (!response.ok) {\n            // Logowanie, jeśli odpowiedź nie jest poprawna\n            console.error(\"HTTP error! status: \".concat(response.status));\n            return response.json().then(function (data) {\n                console.error('Error details from backend:', data);\n                throw new Error(data.error || 'Unknown error');\n            });\n        }\n        return response.json();\n    })\n        .then(function (data) {\n        console.log('Video progress saved:', data);\n    })\n        .catch(function (error) {\n        console.error('Fetch error:', error.message);\n    });\n}\nvar videoPlayer = document.getElementById('videoPlayer');\nif (videoPlayer) {\n    videoPlayer.addEventListener('pause', function () {\n        console.log('Paused at:', videoPlayer.currentTime);\n        sendVideoProgress(videoPlayer.currentTime);\n    });\n    videoPlayer.addEventListener('ended', function () {\n        console.log('Video ended at:', videoPlayer.currentTime);\n        sendVideoProgress(videoPlayer.currentTime);\n    });\n}\nfunction getCSRFToken() {\n    var name = 'csrftoken';\n    var cookies = document.cookie.split(';');\n    for (var _i = 0, cookies_1 = cookies; _i < cookies_1.length; _i++) {\n        var cookie = cookies_1[_i];\n        var _a = cookie.trim().split('='), key = _a[0], value = _a[1];\n        if (key === name) {\n            return decodeURIComponent(value);\n        }\n    }\n    return null;\n}\n\n\n//# sourceURL=webpack:///./src/index.ts?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./src/index.ts"]();
/******/ 	
/******/ })()
;