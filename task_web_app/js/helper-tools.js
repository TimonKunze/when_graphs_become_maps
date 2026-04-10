// helper-tools.js

const htools = (function() {
  // Store public functions and variables
  let public = {};
  // Arrays {{{

  /** Version I:
   * Compares two arrays for equality by converting them to JSON strings.
   * 
   * WARNING: This method should not be used with arrays containing objects,
   * as the behavior may be undefined due to potential differences in key ordering
   * or object references. This function is suitable for arrays containing
   * primitive types like numbers, strings, and booleans.
   */
  public.arraysEqual = function (a1,a2) {
    /* WARNING: arrays must not contain {objects} or behavior may be undefined */
    return JSON.stringify(a1)==JSON.stringify(a2);
  }

  /* Version II:
   * Compare two arrays (list1 and list2) for element-wise equality. 
   * It checks if both arrays have the same length and then iterates 
   * through each element to ensure that the corresponding elements 
   * in the two arrays are identical. If both conditions are met, 
   * the function returns true, indicating that the arrays are equal. 
   * Otherwise, returns false.
   */
  public.listsEqual = function(list1, list2) {
      if (list1.length !== list2.length) return false;
      for (let i = 0; i < list1.length; i++) {
          if (list1[i] !== list2[i]) return false;
      }
      return true;
  }

  /* Only add element to array if not already exists.
   */
  public.addUniqueArray = function(targetArray, arrayToAdd) {
    // Check if arrayToAdd already exists in targetArray
    const exists = targetArray.some(
      element => Array.isArray(element) && JSON.stringify(element) === JSON.stringify(arrayToAdd)
    );
    // Add arrayToAdd only if it doesn't exist
    if (!exists) {
      targetArray.push(arrayToAdd);
      return true; // Indicates the array was added
    }
    return false; // Indicates the array was not added
  }

public.midpointShift = function(a, b) {
  return a.map((val, i) => (val - b[i]) / 2 + b[i]);
}
  // }}}
  // Geometry {{{

  /* Shortens a line defined by two points (x1, y1) and (x2, y2) 
   * by a specified amount on both sides. */
  public.shortenLine = function(x1, y1, x2, y2, shortenAmount) {
    const start = {x:x1, y:y1};
    const end = {x:x2, y:y2};
    // Calculate the direction vector from start to end
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    // Calculate the distance between the points (magnitude of the vector)
    const length = Math.sqrt(dx * dx + dy * dy);
    // Normalize the direction vector
    const unitVector = { x: dx / length, y: dy / length };
    // Calculate the new start and end points
    const newStart = {
      x: start.x + unitVector.x * shortenAmount,
      y: start.y + unitVector.y * shortenAmount
    };
    const newEnd = {
      x: end.x - unitVector.x * shortenAmount,
      y: end.y - unitVector.y * shortenAmount
    };
    // return { newStart, newEnd };
    return [newStart.x, newStart.y, newEnd.x, newEnd.y];
  }

  // }}}
  // Randomization Stuff {{{
 
  /**
   * Shuffles an array in place using the Fisher-Yates algorithm.
   *
   * This function randomly shuffles the elements of the given array using the Fisher-Yates (Knuth) shuffle algorithm.
   * The shuffle is done in place, meaning the original array is modified and returned.
   *
   * Parameters:
   * @param {Array} array - The array to be shuffled.
   *
   * Returns:
   * @returns {Array} The shuffled array.
   */
  public.shuffleArray = function(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  public.seededShuffleArray = function(array, seed="") {
    for (let i = array.length - 1; i > 0; i--) {
      let seedRandomFloat = new Math.seedrandom(subject_id + i.toString());
      let j = Math.floor(seedRandomFloat() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }


  /* Get array with first half ones, and second half 0.
   * */
  public.generateBinaryArray = function(arrLen1, arrLen0=null) {
    if (arrLen0 == null) {
      arrLen0 = arrLen1;
      if (arrLen1 % 2 != 0) {
        console.error("Alert: length should be an even number.")
      }
    }
    const ones = Array(arrLen1).fill(1);
    const zeros = Array(arrLen0).fill(0);
    const binaryArray = ones.concat(zeros);

    return binaryArray;
  }

  /**
   * Generates a random binary list with equal numbers of 0s and 1s.
   *
   * This function creates a binary list of specified length, ensuring it contains an equal number of 0s and 1s. 
   * The list is then shuffled to randomize the order of the elements.
   *
   * Parameters:
   * @param {number} length - The total length of the binary list. Must be an even number.
   * @param {any} [seed=null] - An optional seed parameter (currently unused).
   *
   * Returns:
   * @returns {Array<number>} A shuffled binary list containing an equal number of 0s and 1s.
   */
  public.generateRandomBinaryList = function(arrLen1, arrLen0=null) {
    if (arrLen0 == null) {
      arrLen0 = arrLen1;
      if (arrLen1 % 2 != 0) {
        console.error("Alert: length should be an even number.")
      }
    }
    const binaryList = public.generateBinaryArray(arrLen1, arrLen0);

    return public.shuffleArray(binaryList);
  }

  /* Get random number in specified interval */

  /**
   * Generates a random integer within a specified range.
   *
   * This function returns a random integer between the specified minimum and maximum values, inclusive.
   *
   * Parameters:
   * @param {number} min - The minimum value of the range (inclusive).
   * @param {number} max - The maximum value of the range (inclusive).
   *
   * Returns:
   * @returns {number} A random integer between min and max (both inclusive).
   */
  public.randomIntFromInterval = function(min, max) { // min and max included 
    return Math.floor(Math.random() * (max - min + 1) + min);
  }

  // }}}
  // Type-conversion {{{
  
  /**
   * Converts a nested array to a string representation, e.g. for printing.
   *
   * This function takes a potentially nested array and recursively converts it into a string format.
   * If the input is not an array, it is converted to a string as-is. For arrays, each element is 
   * recursively processed, and the resulting strings are joined together with commas, enclosed in 
   * square brackets.
   *
   * Parameters:
   * @param {Array|any} arr - The input which can be a nested array or any other type.
   *
   * Returns:
   * @returns {String} A string representation of the nested array.
   *
   * Example Usage:
   * public.nestedArrayToString([1, [2, 3], [4, [5, 6]]]);
   * // Returns: "[1, [2, 3], [4, [5, 6]]]"
   *
   * Notes:
   * - If the input is not an array, the function directly returns its string representation.
   * - For arrays, the function recursively processes each element and joins them with commas.
   */
  public.nestedArrayToString = function(arr) {
    // Base case: if the input is not an array, return it as is
    if (!Array.isArray(arr)) {
        return arr.toString();
    }
    // Recursively convert each element of the array to a string
    const stringArray = arr.map(element => nestedArrayToString(element));
    // Join the elements of the array into a string, separated by commas
    return '[' + stringArray.join(', ') + ']';
  }

  
  /**
   * Converts an array of JSON objects into a CSV formatted string.
   * Each object in the input array represents a row in the CSV.
   * Keys of the JSON objects become column headers.
   *
   * @param {Array.<Object>|string} objArray - The array of JSON objects to convert to CSV.
   *   If a string is provided, it will be parsed into JSON first.
   * @returns {string} A CSV formatted string representing the input JSON data.
   *
   * Function taken from jspsych/jspsych.js (where it is used but not exported),
   * (https://github.com/jspsych/jsPsych, accessed 2024-06-28).
   */
  public.JSON2CSV = function(objArray) {
      const array = typeof objArray != "object" ? JSON.parse(objArray) : objArray;
      let line = "";
      let result = "";
      const columns = [];
      for (const row of array) {
          for (const key in row) {
              let keyString = key + "";
              keyString = '"' + keyString.replace(/"/g, '""') + '",';
              if (!columns.includes(key)) {
                  columns.push(key);
                  line += keyString;
              }
          }
      }
      line = line.slice(0, -1); // removes last comma
      result += line + "\r\n";
      for (const row of array) {
          line = "";
          for (const col of columns) {
              let value = typeof row[col] === "undefined" ? "" : row[col];
              if (typeof value == "object") {
                  value = JSON.stringify(value);
              }
              const valueString = value + "";
              line += '"' + valueString.replace(/"/g, '""') + '",';
          }
          line = line.slice(0, -1);
          result += line + "\r\n";
      }
      return result;
  }


  // }}} 
  // Printing and Output {{{


  /**
   * This function creates a downloadable file in the browser using the provided data, filename, and MIME type.
   * It handles file downloading in a way that is compatible with both Internet Explorer 10+ and other modern browsers.
   * (by Kanchu on Stack overflow, 14.07.2015
   * https://stackoverflow.com/questions/13405129/create-and-save-a-file-with-javascript, 
   * accessed 2024-05-16)
   *
   * Parameters:
   * @param {String|Blob} data - The data to be included in the file. This can be a string or a Blob object.
   * @param {String} filename - The desired name for the downloaded file, including its extension (e.g., 'example.txt').
   * @param {String} type - The MIME type of the file (e.g., 'text/plain', 'application/pdf').
   */
  public.downloadFile = function(data, filename, type) {
    var file = new Blob([data], {type: type});
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        var a = document.createElement("a"),
                url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function() {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);  
        }, 0); 
    }
  }
  // }}}
  // Encoding and Decoding {{{

  public.decodeString = function (encoded) {
      function yToX(y) {
          return String.fromCharCode(parseInt(y, 16));
      }
      // Ensure input length is even
      if (encoded.length % 2 !== 0) {
          throw new Error('Invalid Base16 encoded string length.');
      }
      let decoded = '';
      for (let i = 0; i < encoded.length; i += 2) {
          const yPair = encoded.substr(i, 2);
          decoded += yToX(yPair);
      }
      return decoded;
  }

  // }}}
  return public;
})();
