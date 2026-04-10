// scripts.js

// Checks {{{

// Check before starting prolific trials:
// - [ ] randFlag == true
// - [ ] debugFlag == false
// - [ ] prolific == true
// - [ ] nbCongrTTrials correct?
// - [ ] nb learning trials correct?
// - [ ] Do things get saved
// - [ ] part-1-and-2-split correctly?
// - [ ] Check that exp_data is empty
// - [ ] Console logs deleted
// - [ ] Is php private?
// - [ ] All trials uncommented


// }}}
// Flags and Parameters {{{

const debugFlag = false; // --> false
let randFlag = false; // --> true
const part1Flag = false; // --> either one
const part2Flag = true; // --> either one
const prolificFlag = true; // --> true
const feedbackFlag = true; // --> ?
const staticFlag = false; // --> false
const showNumFlag = false;  // --> false

const graphHex = "10248905";
// const varType = "rotational";
const varType = "unconstrained";

console.log("debugFlag", debugFlag);
console.log("randFlag", randFlag);
console.log("part1Flag", part1Flag);
console.log("part2Flag", part2Flag);
console.log("prolificFlag", prolificFlag);
console.log("feedbackFlag", feedbackFlag);
console.log("Graphhex", graphHex);
console.log("VarType", varType);

// }}}
// Initialize Variables {{{


// Initialize JsPsych
// ==================

const jsPsych = initJsPsych({
  show_progress_bar: true,

  on_finish: function() { 
    // Display data
    jsPsych.data.displayData('json');
  },
  on_data_update: function(data) {

    if (part1Flag && part2Flag) {
      part = 0
    } else if (part1Flag && !part2Flag) {
      part = 1
    } else if (!part1Flag && part1Flag) {
      part = 2
    }    

    // Add line delimiter for json-line (jsonl) format
    const dataJsonl = JSON.stringify(data) + "\n"
    const file_name = `${varType}_${subject_id}_p${part}.jsonl`;
    save_data(dataJsonl, data_dir, file_name);
  }
});


// Get IDs and define directories
// ==============================
// const data_dir = varType;
const data_dir = "data";

let subject_id;
let study_id;
let session_id;
if (prolificFlag) {
  // Capture info from Prolific
  subject_id = jsPsych.data.getURLVariable('PROLIFIC_PID');
  study_id = jsPsych.data.getURLVariable('STUDY_ID');
  session_id = jsPsych.data.getURLVariable('SESSION_ID');
} else { 
  // Generate random subject ID with 8 alphanumeric characters
  subject_id = jsPsych.randomization.randomID(8);
  study_id = "custom_study";
  session_id = "custom_session";
}

let prolif_compl_link = htools.decodeString("68747470733A2F2F6170702E70726F6C696669632E636F6D2F7375626D697373696F6E732F636F6D706C6574653F63633D4331444354523059")

// Node Paths (i.e. image stimuli representing nodes)
let nodePaths = [];
let nodePathsSmall = [];
for (let i = 0; i < 8; i++) {
  nodePaths.push(`./stimuli/flowers/node${i+1}.png`);
  nodePathsSmall.push(`./stimuli/flowers/small_imgs/node${i+1}.png`);
}
// Randomize node order
if (randFlag) {
  nodePaths = htools.seededShuffleArray(nodePaths, subject_id);
  nodePathsSmall = htools.seededShuffleArray(nodePathsSmall, subject_id);
}
const dashPath = `./stimuli/other/dash.png`;
const dotPath = `./stimuli/other/dot.png`;
const undoPath = `./stimuli/other/undo_arrow.png`;


// Define Graph and Trial Specs
// ============================

// Get adjacency matrix and positions
let adjMat = params.graphs[graphHex]["adjM"];

// Learning Trial Specs
let allNodePoss;
if (varType === "unconstrained") {
  allNodePoss = htools.shuffleArray(params.graphs["unconstrPos"]);
} else {
  allNodePoss = params.graphs[graphHex]["constantPos"];
}

let relations = getRelations(adjMat);

if (randFlag) relations = htools.shuffleArray(relations);

let nbAllNodes = adjMat.length;


// Sample Learning Trials Specs
const sampleNodePos = [[600, 550], [300, 200], [650, 250]];
const sampleRels = [[0,1], [1,0]];
const sampleStartEndQuest = [1, 0];

let eCongrPairs = params.graphs[graphHex]["eCongrPairs"];
let eIncongrPairs = params.graphs[graphHex]["eIncongrPairs"];
let wCongrPairs = params.graphs[graphHex]["wCongrPairs"];
let wIncongrPairs = params.graphs[graphHex]["wIncongrPairs"];

// Concat unweighted and weighted congr/incongr pairs
let allCongrPairs = gtools.getListOfUniqueEntries(
  gtools.sortPathPairs(eCongrPairs).concat(gtools.sortPathPairs(wCongrPairs))
);
let allIncongrPairs = gtools.getListOfUniqueEntries(
  gtools.sortPathPairs(eIncongrPairs).concat(gtools.sortPathPairs(wIncongrPairs))
);
let allPairs = gtools.getListOfUniqueEntries(
  gtools.sortPathPairs(allCongrPairs).concat(gtools.sortPathPairs(allIncongrPairs))
)

// Randomize congr/incongr pairs
if (randFlag) {
  gtools.randomlyReverseLists(allCongrPairs);
  gtools.randomlyReverseLists(allIncongrPairs);
}

const allPathPairs = allCongrPairs.concat(allIncongrPairs);
let test3Pairs;
if (randFlag) {
  test3Pairs = htools.shuffleArray(allPathPairs);
} else {
  test3Pairs = allPathPairs
}


// Part I: Initializations 
// -----------------------
const nbLearnPasses = debugFlag ? 1 : 3; // in earlier pilots: 3
const nbLearnBlocks =  5; // in earlier pilots: 3
const nbRelations = debugFlag ? 4 : relations.length;
const learnTrialsBlock = nbLearnPasses*nbRelations;
// console.log("learnTrialsBlock", learnTrialsBlock)

if (varType=="unconstrained") {
  allNodePoss = allNodePoss.slice(0, 2*learnTrialsBlock*nbLearnBlocks);  // Don't use all allNodePoss
}

const keyChoice = debugFlag ? null : "NO_KEYS";


// Part II: Initializations 
// ------------------------
const nbCongrTTrials = [allCongrPairs.length, allIncongrPairs.length];


// Print Info
// ----------
// console.log("General")
// console.log("subject_id", subject_id)
// console.log("study_id", study_id)
// console.log("session_id", session_id)

// console.log("Part I")
// console.log("nbLearnPasses", nbLearnPasses);
// console.log("nbLearnBlocks", nbLearnBlocks);
// console.log("nb relations", nbRelations)
// console.log("Part II")
// console.log("nbCongrTTrials", nbCongrTTrials);


// Environment Design Specs
// -----------------
const colors = {
    "edgeTrue": "#5ce65c",
    "edgeFalse": "#ed2100",
    "edgeUndef": "blue",
    "nice" : "#f51467",
    "envText" : "grey",
    "bgWhite": "#ffffff",
    "bgGreen": "#98BE64",
    "bgGrid": "#799850",
    "drawStroke": "#eeeeee",
};

let sizes = {
  "node" : 60, // radius in px (formerly: 50) 
  "env" : [900, 900], // x and y in px
  "envExtra" : 100, // x and y in px
  "bee" : 48,
};


// }}}
// Global functions {{{

/*Store the relations found in a adjacency matrix in a list.*/
function getRelations(matrix, value=1, excludeSelfRel=false) {
  let relations = [];
  for (let i=0; i<matrix.length; i++) {
    for (let j = 0; j < matrix[i].length; j++) {
      if (matrix[i][j] === value) {
        if (excludeSelfRel) {
          if (i!==j) {
          relations.push([i, j]);
          }
        } else {
          relations.push([i, j]);
        }
      }
    } 
  }
  return relations;
}

/*Rotate points around a center point in 2D. Angle in radians.*/
function rotatePoint(center, point, angle) {
    // Calculate distance from center to point
    let dx = point[0] - center[0];
    let dy = point[1] - center[1];

    // Calculate new coordinates
    let newX = center[0] + dx * Math.cos(angle) - dy * Math.sin(angle);
    let newY = center[1] + dx * Math.sin(angle) + dy * Math.cos(angle);

    return [newX, newY];
}

/*Calculate horizontal angle from given points line segment.*/
function getHorAngleFromLineSeg(p1, p2) {
  let dx = p1[0] - p2[0];
  let dy = p1[1] - p2[1];
  let angle = Math.atan(dy / dx); //* 180 / PI;

  return angle;
}

/* Get a point on the line between two other points. */
function point_on_line(point1, point2, t) {
    const x = point1[0] + t * (point2[0] - point1[0]);
    const y = point1[1] + t * (point2[1] - point1[1]);
    return [x, y];
}

/* Get 4 equidistant points. */
function getEquidistantPoints(point1, point2, distance) {
    // Calculate midpoint
    const midpoint = [(point1[0] + point2[0]) / 2, (point1[1] + point2[1]) / 2];
    // Calculate direction vector
    const vector = [point2[0] - point1[0], point2[1] - point1[1]];
    const length = Math.sqrt(vector[0] ** 2 + vector[1] ** 2);
    const direction = [vector[0] / length, vector[1] / length];
    // Calculate equidistant points
    const equidistantPoints = [
        [midpoint[0] + distance * direction[0], midpoint[1] + distance * direction[1]],
        [midpoint[0] - distance * direction[0], midpoint[1] - distance * direction[1]],
        [midpoint[0] + distance * direction[1], midpoint[1] - distance * direction[0]],
        [midpoint[0] - distance * direction[1], midpoint[1] + distance * direction[0]]
    ];
    return equidistantPoints;
}


/**
 * By calling this function you can send a message to a 
 * specific user via telegram
 * @param {String} the text to send
 *
*/
function sendMessage(text) {
  let tg = {
      // Your bot's token that got from @BotFather
      token: "7087198601:AAFYd0U-IbCKAnzc-m9Rn_8ebW80eZm6as0",
      // The user's(that you want to send a message) telegram chat id
      chat_id: "292107138"
  }
  const url = `https://api.telegram.org/bot${tg.token}/sendMessage?chat_id=${tg.chat_id}&text=${text}`; // The url to request
  const xht = new XMLHttpRequest();
  xht.open("GET", url);
  xht.send();
}


// }}}
// Save data {{{


// Add IDs and other data to all trials
jsPsych.data.addProperties({
  // Subject Specific Data
  subject_id: subject_id,
  study_id: study_id,
  session_id: session_id,
  group_name: varType,
  date: new Date().toDateString(),
  time: new Date().toTimeString(),
  // Animation environment
  node_positions: allNodePoss,
  canvas_size: sizes["env"],
  node_size: sizes["node"],
  // Learning
  nb_learn_passes: nbLearnPasses,
  nb_learn_blocks: nbLearnBlocks,
  nb_relation: nbRelations,
  nb_learn_trials_in_block: learnTrialsBlock,
  nb_learn_trials: learnTrialsBlock*nbLearnBlocks,
  relations: relations,
  // Matrices
  adjacency_matrix: adjMat,
  // Congruency
  eucd_congr_pairs: eCongrPairs,
  eucd_incongr_pairs: eIncongrPairs,
  wspd_congr_pairs: wCongrPairs,
  wspd_incongr_pairs: wIncongrPairs,
  test3_pairs: test3Pairs,
  // Paths
  node_paths: nodePaths,
  node_paths_small: nodePathsSmall,
  // Flags
  debug_flag: debugFlag,
  rand_flag: randFlag,
  part1_flag: part1Flag,
  part2_flag: part2Flag,
  prolific_flag: prolificFlag,
  feedback_flag: feedbackFlag,
});


/* Save data with ajax of jQuery */
function save_data(data, data_dir, file_name) {
  jQuery.ajax({
    type: 'post',
    cache: false,
    url: "./exp_data/save_data.php", // save_url 
    data: {
      data_dir: data_dir,
      file_name: file_name, // the file type should be added
      exp_data: data,
    }
  });
}

//}}}
// Preload Trial {{{


const preload_trial = {
  type: jsPsychPreload,
  auto_preload: true,
  images: [...nodePaths, ...nodePathsSmall, ...[dashPath], ...[dotPath], ...[undoPath] ],
  show_detailed_errors: true,
  error_message: 'The experiment failed to load. Please shoot me an email: tkunze@sissa.it.',
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "preload"
    });
  },
}


// }}}
// Welcome Trial {{{

let partString = "";
if (part1Flag && !part2Flag) {
  partString = "part 1 of ";
} else if (!part1Flag && part2Flag) {
  partString = "part 2 of ";
} 

const welcome_trial = {
  type: jsPsychHtmlButtonResponse,
  stimulus: `<p>Welcome to ${partString}our experiment!</p>`,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "welcome"
    });
  },
}

//}}}
// Consent Trial {{{

const consent_trial = {
  type: jsPsychSurveyMultiSelect,
  questions: [
    {
      prompt: `
        <p>You are about to participate in a psychological study which involves 
        tracking a bee that moves from one flower to another.
        </p>
        <p>Please download and read the <a href="./participant_info.pdf">participant 
        information sheet</a>, which provides information on this study and 
        how your data will be used. By accepting and 
        participating in this study, you agree to the following:
        </p>
        <ol>
        <li>I confirm that I am at least 18 years old.
        </li>
        <li>I have read the above information relating to the purpose and 
        procedures of the study.
        </li>
        <li>I have been informed about the aims and objectives of this research.
        </li>
        <li>I have had the opportunity to ask questions about the experimental 
        procedure and I have obtained satisfactory answers.
        </li>
        <li>I am aware of any risks related to taking part in this experiment.
        </li>
        <li>I have received satisfactory assurances on the confidentality of my data.
        </li>
        <li>I understand that the anonymous data I produce may be kept permanently
        in archives and made freely available online.
        </li>
        <li>I am aware that I am free to withdraw from this study at any stage.
        </li>
        </ol> 
        `, 
      options: ["I consent to taking part in this study."], 
      horizontal: true,
      required: !debugFlag,
    }], 
      on_finish: function(data) {
        jsPsych.data.addDataToLastTrial({
          trial_name: "consent",
        });

      },
};

//}}}
// Fullscreen Trial {{{


const fullscreen_trial = {
  type: jsPsychFullscreen,
  fullscreen_mode: true,
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "fullscreen",
    });
  },
};

//}}}
// Participant Query Trials {{{


const age_trial = {
  type: jsPsychSurveyText,
  questions: [{
    prompt: "Please enter your age:",
    name: "age",
    placeholder: "e.g., 25",
    columns: 7,
    required: !debugFlag,
  }],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "age",
    });
  },
};

const gender_trial = {
  type: jsPsychSurveyMultiChoice,
  questions: [{
    prompt: "Please indicate your gender:", 
      name: 'gender', 
      options: ['female', 'male', 'other'], 
      required: !debugFlag,
    },],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "gender",
    });
  },
};


//}}}
// Instruction Learning Trial {{{


const learnInstrTrial = {
  // type: jsPsychHtmlKeyboardResponse,
  type: jsPsychHtmlButtonResponse,
  stimulus: itools.instrTask1Part1,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "learn_instructions",
    });
  },
};


const learnInstrEndTrial = {
  type: jsPsychHtmlButtonResponse,
  stimulus: itools.instrTask1Part1End,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "learn_instr_end",
    });
  },
};


//}}}
// Learning: Animation Trial {{{

function createLearnTrialAnim(nodePos, relations, trialI, learnPassI,
                              rotAngle=0) {
  let nbNodes = nodePos.length;
  let saveNodesClicked = [];
  let trialEnded = false;
  let startTimeRT;
  let endTimeRT;

  const learnTrialAnim = {
    type: jsPsychP5JS,
    top_level_declarations: function (p){
      p.TLD = {} // create empty object tagged on p so the var's and funcs are accessible within setup and draw
      // TLD: Global Variables {{{

      // Create init conditions for lazers
      p.TLD.movObjAlterFlag = true;
      p.TLD.movObjCounter = 0;
      // Create matrix with stop flags set False
      p.TLD.stopFlagM = gtools.createMatrix(nbNodes, nbNodes, false);
      // Create matrix with run variables (continuously updated)
      p.TLD.runM = gtools.createMatrix(nbNodes, nbNodes, 0);
      for (let i = 0; i < nbNodes; i++) {
        for (let j = 0; j < nbNodes; j++) {
          p.TLD.runM[j][i] = [...nodePos[i]];
        }
      }
      // Initialize show towers list
      p.TLD.nodeClicked = Array(nbNodes).fill(false);

      // Init noise
      p.noiseSeed(1);
      p.TLD.vibrateStart = 0.0;
      p.TLD.vibrateEnd = 0.0;
      p.TLD.shakeTimerStart = new Array(nbNodes).fill(0);
      p.TLD.shakeTimerEnd = new Array(nbNodes).fill(0);

      // }}}
      // TLD: Functions {{{

      // Define Nodes
      p.TLD.Node = class {
        constructor(x, y, diam, aspect, num=false) {
          this.x = x;
          this.y = y;
          this.diam = diam;
          this.aspect = aspect; // color or image
          this.num = num;
          this.msOver;
        }
        display(noise=0) {
          if (typeof this.aspect == "string") {
            p.stroke("#000000");
            p.strokeWeight(1);
            p.fill(this.aspect);
            p.circle(this.x + noise, this.y + noise, this.diam + noise);
          } else {
            p.image(this.aspect, 
                    this.x-sizes["node"]/2 + noise, 
                    this.y-sizes["node"]/2 + noise,
                    sizes["node"],
                    sizes["node"],
            );
          }

          if (typeof this.num == "number") {
            p.textSize(18);
            p.textStyle("italic");
            p.fill("#000000");
            p.text(this.num.toString(), this.x, this.y);
           }
        }
      }

      p.TLD.drawBee = function (pos, angle) {
        // set rat size
        // let size = 40; 
        let size = sizes["bee"]; 
        let iter = 4;
        
        p.TLD.bee.resize(size, 0);
        p.TLD.bee_mirrored.resize(size, 0);
        p.push();
        // Move bee to position
        p.translate(pos[0], pos[1]);
        // Rotate in vertical direction
        p.rotate(p.radians(7));
        // Rotate in direction to goal
        p.rotate(angle);
        // draw image
        let size_mult = 1/1;
        if (p.TLD.movObjAlterFlag) {
          p.image(
            p.TLD.bee, 
            -p.TLD.bee.width/2, -p.TLD.bee.height/2, 
            p.TLD.bee.width*size_mult, p.TLD.bee.width*size_mult);
          if (p.TLD.movObjCounter === iter) {
            p.TLD.movObjAlterFlag = false;
            p.TLD.movObjCounter = 0;
          }
          p.TLD.movObjCounter++;
        } else {
          p.image(
            p.TLD.bee_mirrored, 
            -p.TLD.bee_mirrored.width/2, -p.TLD.bee_mirrored.height/2, 
            p.TLD.bee_mirrored.width*size_mult, p.TLD.bee_mirrored.width*size_mult,
          );
          if (p.TLD.movObjCounter === iter) {
            p.TLD.movObjAlterFlag = true;
            p.TLD.movObjCounter = 0;
          }
          p.TLD.movObjCounter++;
        }
        p.pop();
      }

      p.TLD.runBee = function (p1, p2, pt1, stopFlag) {
        // Set speed by nb of translated pixels
        let speed = 4;
        // Compute angle
        let angle = getHorAngleFromLineSeg(p1, p2) + p.PI;
        // Determine stop of drawn line and set back to start
        const dirFlags = [p1[0] < p2[0], p1[1] < p2[1]].toString();

        // Draw moving Stimulus
        if (stopFlag === false) {
          if (dirFlags === [true, true].toString() 
              || dirFlags === [true, false].toString()) {
            ratAngle = angle - 3*p.PI/2;
          } else if (dirFlags === [false, false].toString() 
                     || dirFlags === [false, true].toString()) {
            ratAngle = angle + 3*p.PI/2;
          }
          p.TLD.drawBee(pt1, ratAngle);
        }
        if (dirFlags === [true, true].toString()) {
          // Update line start
          pt1[0] += -speed*p.cos(angle);
          pt1[1] += -speed*p.sin(angle);
          if (pt1[0] >= p2[0] && pt1[1] >= p2[1]) {
            stopFlag = true;
          }
        } else if (dirFlags === [false, false].toString()) {
          // Update line start
          pt1[0] += speed*p.cos(angle);
          pt1[1] += speed*p.sin(angle);
          if (pt1[0] <= p2[0] && pt1[1] <= p2[1]) {
            stopFlag = true;
          }
        } else if (dirFlags === [true, false].toString()) {
          // Update line start
          pt1[0] += -speed*p.cos(angle);
          pt1[1] += -speed*p.sin(angle);
          if (pt1[0] >= p2[0] && pt1[1] <= p2[1]) {
            stopFlag = true;
          }
        } else if (dirFlags === [false, true].toString()) {
          // Update line start
          pt1[0] += speed*p.cos(angle);
          pt1[1] += speed*p.sin(angle);
          if (pt1[0] <= p2[0] && pt1[1] >= p2[1]) {
            stopFlag = true;
          }
        } else {
          console.log("error in second cases");
        }
        return [pt1, stopFlag];
      }

      p.mousePressed = function () {
        for (let i = 0; i < nbNodes; i++) {
          tPLowX = nodePos[i][0] - sizes["node"]/2;
          tPHighX = nodePos[i][0] + sizes["node"]/2;
          tPLowY = nodePos[i][1] - sizes["node"]/2;
          tPHighY = nodePos[i][1] + sizes["node"]/2;

          if (p.mouseX < tPHighX && p.mouseX > tPLowX 
              && p.mouseY < tPHighY && p.mouseY > tPLowY) {
            // if node was clicked
            p.TLD.nodeClicked[i] = true;
          } 
        }
      }

      p.TLD.drawRelations = function (adjMat, nodePos) {
        for (let i=0; i < nodePos.length; i++) {
          for (let j=0; j < nodePos.length; j++) {
            if (adjMat[i][j]==1) {
              p.stroke("#f51467");
              p.strokeWeight(2);
              p.line(nodePos[i][0], nodePos[i][1], 
                     nodePos[j][0], nodePos[j][1]);
            } else {
              p.stroke("grey");
              p.strokeWeight(0.2);
              }
            }
          }
        }

        p.TLD.changeCursorHand = function (positions, thresh) {
          let dists = []
          for (const ps of positions) {
            dists.push(p.dist(p.mouseX, p.mouseY, ...ps));
          }
          if (dists.some(d => d < thresh)) {
            p.cursor(p.HAND);
          }
        }

      // }}}
    },
    setup_func: function(p) {
      // Set Up Fun ===================================================== {{{
      // Set up Background
      p.createCanvas(sizes["env"][0], sizes["env"][1]);

      // Set up moving Object
      p.TLD.bee = p.loadImage("./stimuli/other/moving_obj.png");
      p.imageMode(p.CORNER);
      p.TLD.bee_mirrored = p.loadImage("./stimuli/other/moving_obj_mirrored.png");
      p.imageMode(p.CORNER);

      // Set up Nodes
      p.TLD.nodes = [];
      for (let i=0; i<nbNodes; i++) {
        const showNum = (debugFlag | showNumFlag) ? i : false;
        let nodeObj = new p.TLD.Node(
         nodePos[i][0], nodePos[i][1],
         sizes["node"],
         p.loadImage(nodePathsSmall[i]),
         num=showNum,
        );
        p.TLD.nodes.push(nodeObj);
      }



      // }}}
     },
    draw_func: function(p){
      // Drawing Fun ==================================================== {{{
      
      // Set Cursor
      p.cursor(p.ARROW);
      p.TLD.changeCursorHand(nodePos, sizes["node"]/2);

      // Set Background
      p.background(colors["bgGreen"]);
      p.textSize(38);
      p.textFont('Courier New');
      p.fill('grey');
      p.text('Search', 20, 40);

      // Draw Relations for debugging
      if (debugFlag === true) {
        p.TLD.drawRelations(adjMat, nodePos);
      }

      // Draw nodes
      for (let nodeI = 0; nodeI < nbNodes; nodeI++) {

        startN = relations[trialI][0];
        endN = relations[trialI][1];

        // Stop trial if bee is found
        if (p.TLD.shakeTimerEnd[nodeI] > 100) {
          p.remove(); // Remove env to not clutter
          jsPsych.finishTrial();
        }
        // Draw flower that is clicked
        else if (p.TLD.nodeClicked[nodeI] && nodeI !== endN) {
          // Draw relations
          if (nodeI === startN) {
            [p.TLD.runM[endN][startN], p.TLD.stopFlagM[endN][startN]] = p.TLD.runBee(
              nodePos[startN], nodePos[endN], p.TLD.runM[endN][startN], p.TLD.stopFlagM[endN][startN],
            );
          }
          if (staticFlag) {
            let x;
            let midpoint = htools.midpointShift(nodePos[endN], nodePos[startN]);
            [midpoint, x] = p.TLD.runBee(
              nodePos[startN], nodePos[endN], midpoint, false,);

          }
          // Let flower vibrate when clicked
          p.TLD.shakeTimerStart[nodeI] += 1;
          if (p.TLD.shakeTimerStart[nodeI] < 40) {
            p.TLD.vibrateStart += 0.1;
            noise = p.noise(p.TLD.vibrateStart) * 10;
          } else {
            noise = 0;
          }
          saveNodesClicked.push(nodeI);
        // Let flower vibrate at end for some time
        } else if (nodeI===endN) {
          // Continue vibrating for some time, then stop
          if (p.TLD.shakeTimerEnd[nodeI] > 1 && p.TLD.shakeTimerEnd[nodeI] < 40) {
            p.TLD.vibrateEnd += 0.1;
            noise = p.noise(p.TLD.vibrateEnd) * 10;
          } else {
            noise = 0;
          }
          // Increase shakeTimer
          if (p.TLD.stopFlagM[endN][startN]) {
            p.TLD.shakeTimerEnd[nodeI] += 1;
          }
          // Let flower also vibrate when clicked
          if (p.TLD.nodeClicked[nodeI] ) {
            p.TLD.shakeTimerStart[nodeI] += 1;
            if (p.TLD.shakeTimerStart[nodeI] < 40) {
              p.TLD.vibrateStart += 0.1;
              noise = p.noise(p.TLD.vibrateStart) * 10;
            } 
          }
        // Set vibration to zero for all other flowers
        } else {
          noise = 0;
        }
        // Draw flowers
        p.TLD.nodes[nodeI].display(noise);
      }

      // Stop p5js animation
      if (trialEnded) {
        p.remove(); 
      }

      //}}}
    },
    on_start: function(data) {
      startTimeRT = performance.now(); // Save RT
    },
    on_finish: function(data) {
      endTimeRT = performance.now();
      const rt = endTimeRT-startTimeRT;
      saveNodesClicked = [...new Set(saveNodesClicked)];
      trialEnded = true;
      jsPsych.data.addDataToLastTrial({
        node_pos_learnanim: nodePos,
        trial_name: "learn_anim",
        trial_ind_learnanim: trialI,
        relation_learnanim: relations[trialI],
        learnpass_ind_learnanim: learnPassI,
        angle_learnanim: rotAngle,
        type_learnanim: type,
        rt_learnanim: rt,
        nodes_clicked_learnanim: saveNodesClicked,
      });
    },
    key_choices: keyChoice, //"NO_KEYS",
    // trial_duration: timeout, // 5min in ms

  };
  return learnTrialAnim;
}

// }}}
// Learning: RelDrawing Trial {{{

function createDrawingTrial(nodePos, rel, trialI, learnPassI, angle=0, type="") {

  let trialEnded = false;

  let startTime = 100000000000;
  let frameCoOdd = false;
  let frameCoEve = false;
  let nbAttempts = 1;
  let attempts = [];
  let lineColRed = false;
  let frameCoOddWr = 0;
  let frameCoEveWr = 0;

  let node1Correct = false;
  let node2Correct = false;
  let nodeStarted = -1;
  let nodeEnded = -1;

  const attemptout = 12;

  let startTimeRT;
  let endTimeRT;

  const drawingTrial = {
    type: jsPsychP5JS,
    top_level_declarations: function (p){
      // Top Level Declarations ============================================== {{{
      p.TLD = {} // create an empty object tagged on p so the var's and funcs are accessible within setup and draw

      p.TLD.nbNodes = nodePos.length;
      p.TLD.towPos = nodePos

      // Define Nodes
      p.TLD.Node = class {
        constructor(x, y, diam, aspect, num=false) {
          this.x = x;
          this.y = y;
          this.diam = diam;
          this.aspect = aspect; // color or image
          this.num = num;
          this.msOver;
          this.msOverReleased = false;
        }
        display() {
          if (typeof this.aspect == "string") {
            p.stroke("#000000");
            p.strokeWeight(1);
            p.fill(this.aspect);
            p.circle(this.x, this.y, this.diam);
          } else {
            p.image(this.aspect,
                    this.x - sizes["node"]/2, 
                    this.y - sizes["node"]/2,
                    sizes["node"],
                    sizes["node"],
            );
          }

          if (typeof this.num == "number") {
            p.textSize(18);
            p.textStyle("italic");
            p.fill("#000000");
            p.text(this.num.toString(), this.x, this.y);
           }  
        }
      }

      p.TLD.gridBackground = function(horLines=18, verLines=18) {
        for (let x = 0; x < p.width; x += p.width / verLines) {
          for (let y = 0; y < p.height; y += p.height / horLines) {
            p.stroke(colors["bgGrid"]);
            p.strokeWeight(0.5);
            p.line(x, 0, x, p.height);
            p.line(0, y, p.width, y);
          }
        }
      }

      p.mousePressed = function () {
        for (i=0; i<p.TLD.nodes.length; i++) {
          // Check if cursor is at node
          if (p.dist(p.TLD.nodes[i].x, p.TLD.nodes[i].y, 
                     p.mouseX, p.mouseY) <= p.TLD.nodes[i].diam/2) {
            p.TLD.nodes[i].msOverPressed = true;
          } else {
            p.TLD.nodes[i].msOverPressed = false;
          }
        }
      }

      p.mouseReleased = function () {
        for (i=0; i<p.TLD.nodes.length; i++) {
          // Check if cursor is at node
          if (p.dist(p.TLD.nodes[i].x, p.TLD.nodes[i].y, 
                     p.mouseX, p.mouseY) <= p.TLD.nodes[i].diam/2) {
            p.TLD.nodes[i].msOverReleased = true;
          } else {
            p.TLD.nodes[i].msOverReleased = false;
          }
        }
      }

      p.TLD.changeCursorCross = function (positions, thresh) {
        let dists = []
        for (const ps of positions) {
          dists.push(p.dist(p.mouseX, p.mouseY, ...ps));
        }
        if (dists.some(d => d < thresh)) {
          p.cursor(p.CROSS);
        }
      }

      // }}}
    },
    setup_func: function(p) {
      // Set Up Function ===================================================== {{{

      // Set up Background
      p.createCanvas(sizes["env"][0], sizes["env"][1]);

      // Set up Nodes
      p.TLD.nodes = [];
      for (let i=0; i<p.TLD.towPos.length; i++) {
        let num = debugFlag ? i : false;
        let nodeObj = new p.TLD.Node(
          p.TLD.towPos[i][0], 
          p.TLD.towPos[i][1], 
          sizes["node"],
          p.loadImage(nodePathsSmall[i]),
          num=num,
        );
        p.TLD.nodes.push(nodeObj);
      }

      // Draw Background
      p.fill(colors["bgWhite"]);
      p.rect(sizes["env"][0], 0, sizes["env"][0], sizes["env"][1]);
      p.background(colors["bgGreen"]);
      p.TLD.gridBackground();

      // Draw nodes
      p.noStroke();
      for (let i=0; i<p.TLD.nodes.length; i++) {
        p.TLD.nodes[i].display();
      }
      // }}}
     },
draw_func: function(p) {
  // Drawing Function ==================================================== {{{
  
  // Set Cursor
  p.cursor(p.ARROW);
  p.TLD.changeCursorCross(p.TLD.towPos, sizes["node"]/2);


  // Run drawing over all nodes
  for (let i = 0; i < p.TLD.nodes.length; i++) {
    // Handle drawing and state changes when mouse is pressed over a node
    if (p.TLD.nodes[i].msOverPressed && p.mouseIsPressed) {
      p.cursor(p.CROSS);
      p.stroke(colors["drawStroke"]);
      p.strokeWeight(3);
      p.line(p.mouseX, p.mouseY, p.pmouseX, p.pmouseY);

      nodeStarted = i;
      nodeEnded = -1;

      // Alow for both directions
      node1Correct = (i===rel[0]);
      node2Correct = (i===rel[1]);

    // Handle state changes when mouse is released
    } else if (!p.mouseIsPressed) {
      // Set Background
      p.background(colors["bgGreen"]);
      p.TLD.gridBackground();
      p.textSize(38);
      p.textFont('Courier New');
      p.fill('grey');
      p.text('Draw', 20, 40);

      // Delete drawing
      p.noStroke();
      p.TLD.nodes.forEach(node => node.display());

      // Determine if mouse was released over a node
      if (p.TLD.nodes[i].msOverReleased) {
        nodeEnded = i;
      }

      if (nodeStarted !== -1 && nodeEnded !== -1 && nodeStarted !== nodeEnded) {
  
        // Alow for both directions
        if (node1Correct && !node2Correct) {
          node2Correct = (nodeEnded === rel[1]);
        } else if (node2Correct && !node1Correct) {
          node1Correct = (nodeEnded === rel[0]);
        }

        // Draw straight line if two nodes were connected
        if (node1Correct && node2Correct) {
          p.stroke(colors["edgeTrue"]);
          lineColRed = false;
        } else {
          p.stroke(colors["edgeFalse"]);
          lineColRed = true;
        }
        p.strokeWeight(6);
        p.line(
          nodePos[nodeStarted][0], nodePos[nodeStarted][1],
          nodePos[nodeEnded][0], nodePos[nodeEnded][1]
        );
      }
    // Reset if mouse is clicked elsewhere in environment
    } else if (p.mouseIsPressed 
                && !p.TLD.nodes[i].msOverPressed 
                && nodeEnded !== -1) {

      // Set background
      p.cursor(p.ARROW);
      p.background(colors["bgGreen"]);
      p.TLD.gridBackground();
      p.textSize(38);
      p.textFont('Courier New');
      p.fill('grey');
      p.text('Draw', 20, 40);

      // Delete drawings
      p.noStroke();
      p.TLD.nodes.forEach(node => node.display());
      nodeEnded = -1;
      lineColRed = false;
    }
  }

  // Stop trial after 1.5s if correct relation was drawn
  // or after 10 wrong relations 
  nodesCorrect = node1Correct && node2Correct;
  if (p.frameCount % 2 === 0) {
    frameCoEve = nodesCorrect
    frameCoEveCount = p.frameCount;
    frameCoEveWr = lineColRed;
  } else {
    frameCoOdd = nodesCorrect
    frameCoOddCount = p.frameCount;
    frameCoOddWr = lineColRed;
  }

  // Count number of wrong relations
  if (!nodesCorrect && frameCoOddWr!==frameCoEveWr &&
      ((frameCoEveWr && frameCoEveCount > frameCoOddCount) || 
       (frameCoOddWr && frameCoEveCount < frameCoOddCount))) {
      nbAttempts++;
      attempts.push([nodeStarted, nodeEnded]);
  }
  
  // Get time of correct relation found
  if (frameCoEve !== frameCoOdd) startTime = p.millis();
  
  elapsedTime = p.millis() - startTime;
  if (elapsedTime > 1200 || nbAttempts > attemptout) {
    if (elapsedTime > 1200) {
    }
    // Stop animation
    p.remove();
    // Finish Trial
    jsPsych.finishTrial();
  }
  // Stop p5js animation
  if (trialEnded) p.remove(); 
      
  // }}}
    },
    on_start: function(data) {
      startTimeRT = performance.now();
    },
    on_finish: function(data) {
      trialEnded = true;
      endTimeRT = performance.now();
      const rt = endTimeRT-startTimeRT;
      data = {
        trial_name: "draw_test",
        type_drawtest: type,
        trial_ind_drawtest: trialI,
        learnpass_ind_drawtest: learnPassI,
        nodepos_drawtest: nodePos,
        relation_drawtest: rel,
        nb_attempts_drawtest: nbAttempts,
        acc_drawtest: nbAttempts===1,
        attempts_drawtest: attempts,
        attemptout_drawtest: attemptout,
        rt_drawtest: rt,
      };
      jsPsych.data.addDataToLastTrial(data);
    },
    key_choices: "NO_KEYS",
  };
  return drawingTrial;
}

// }}}
// Learning: Summary trial {{{

function createDrawingTrialSummary(trlsBack, block) {

  const drawingSummary = {
    type: jsPsychHtmlButtonResponse,
    on_start: function(trial) {
      const tCorTrue = jsPsych.data.get().last(trlsBack).filter({
        acc_drawtest: true
      });
      const tCorFalse = jsPsych.data.get().last(trlsBack).filter({
        acc_drawtest: false
      });
      const correct = tCorTrue.trials.length;
      const incorrect = tCorFalse.trials.length;
      const total = correct + incorrect;
      const fraction = correct/total;
      let cheerUp = "";
      if (fraction > 0.9 ) {
        cheerUp = "Excellent job!";
      } else if (fraction <= 0.9 && fraction > 0.8 ) {
        cheerUp = "Really good job!";
      } else if (fraction <= 0.8 && fraction > 0.7) {
        cheerUp = "Quite good!";
      } else if (fraction <= 0.7 && fraction > 0.5) {
        cheerUp = "Okay! But you can do better!";
      } else {
        cheerUp = "Arrgh! I'm sure you can do better!";
      }

      trial.stimulus = `
            <p>
            Well done. 
            You finished the ${block} block.
            </p>
            <br>
            <p>
            You drew <strong>${Math.round(correct/total*100)}%</strong> 
            connections correctly on the first try. 
            </p>
            <p>
            ${cheerUp}
            </p>
          `;
    },
    stimulus: "",
    choices: ['Continue'],
    on_finish: function(data) {
      jsPsych.data.addDataToLastTrial({
        trial_name: "drawing_feedback",
      });
    },
  }
  return drawingSummary;
}


//}}}
// Learning: Learnrelquest Test {{{

const learnTrialRelQueryInstr = {
  type: jsPsychHtmlButtonResponse,
  stimulus: itools.instrTask2Part1,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "learn_trial_relquest_instr",
    });
  },
};

function createLearnTrialRelQuery(rel, known, trialInd, type) {

  const stim_width_ft = "100px";

  const startNode = rel[0];
  const endNode = rel[1];

  const learnTrialRelQuery = {
    type: jsPsychHtmlButtonResponse,
    required: true,
    stimulus: `
      <p>
        Please indicate whether the bee knew, or did not know
        this pair of flowers.
      </p>
      <p>
        <img src=${nodePaths[startNode]} 
          style='max-width:${stim_width_ft};max-height:${stim_width_ft};'>
        <img src=${dotPath} style='max-width:${stim_width_ft};max-height:${stim_width_ft};'>
        <img src=${nodePaths[endNode]} 
          style='max-width:${stim_width_ft};max-height:${stim_width_ft};'>
      </p>
      <br>
    `,
    choices: ["Known", "Not known"],
    save_trial_parameters: {
      choices: true,
      stimulus: true,
    },
    on_finish: function(data) {
      // Score response as correct or incorrect and save
      if (data.response == 0 && known) {
        data.correct = 1;
      } else if (data.response == 1 && !known) {
        data.correct = 1;
      } else {
        data.correct = 0;
      }
      jsPsych.data.addDataToLastTrial({
        trial_name: "learn_relquest", 
        known_learnrelquest: known, 
        pair_learnrelquest: rel,
        trial_ind_learnrelquest: trialInd,
        type_learnrelquest: type,
      });
    },
  };
  return learnTrialRelQuery;
}


function createRelQueryTrialFeedback(testPasses) {
  let nbLastT = testPasses*nbRelations*2;

  const learnTrialFeedback = {
    type: jsPsychHtmlButtonResponse,
    on_start: function(trial){
      const lastTrCorr = jsPsych.data.get().last(nbLastT).filter({correct: 1});
      const lastTrIncorr = jsPsych.data.get().last(nbLastT).filter({correct: 0});
      const correct = lastTrCorr.trials.length;
      const incorrect = lastTrIncorr.trials.length;
      const total = correct + incorrect;
      const fraction = correct / total;
      if (fraction > 0.97) {
        cheerUp = "Excellent job!";
      } else if (fraction <= 0.97 && fraction > 0.85 ) {
        cheerUp = "Really good job!";
      } else if (fraction <= 0.85 && fraction > 0.7) {
        cheerUp = "Quite good!";
      } else if (fraction <= 0.7 && fraction > 0.60) {
        cheerUp = "Okay! But you can do better!";
      } else {
        cheerUp = "I'm sure you can do better!";
      }
      trial.stimulus = `
            <br>
            <p>
            You answered <strong>${Math.round(correct/total*100)}%</strong> 
            of questions correctly.
            </p>
            <p>
            ${cheerUp}
            </p>
          `;
    },
    stimulus: "",
    choices: ['Continue'],
    on_finish: function(data) {
      jsPsych.data.addDataToLastTrial({
        trial_name: "learn_relquest_fb",
      });
    },
  }
  return learnTrialFeedback;
}



// }}}
// Testing: Congruency Test Instructions {{{

let expl_path = "./stimuli/other/test_example.png";
stim_width_ex = "700px"

const testOneInstrTrial1 = {
  type: jsPsychHtmlButtonResponse,
  stimulus: itools.instrTask1Part2,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "test_congr_instr",
    });
  },
};


const testOneInstrTrial2 = {
  type: jsPsychHtmlButtonResponse,
  stimulus: `
    <p>
      We provide you with <strong>two unknown pairs of 
      flowers</strong>, and ask you 
      to judge which indirect route from flower to flower via 
      known connections requires the least stopovers. 
    </p>
    <p>
      The task looks like this:
    </p>
    <p><img src=${expl_path} 
        style='max-width:${stim_width_ex};max-height:${stim_width_ex};'>
    </p>
    <p>
      To answer, we ask you to <strong>click on the button that corresponds 
      to the shorter route</strong>.
    </p>
    <p>
      It's not an easy task. Please take all the time you need for it 
      and try to be as accurate as possible.
    </p>
    <p>
      When you click 'Continue' the experiment directly starts.
    </p>
    `,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "test_congr_instr",
    });
  },
};



//}}}
// Testing: Congruency Task {{{


function createCongrTestTrial(tTrialI, currentPair, randFlag) {

  const path1SDPlongerPath2 = currentPair[0].length > currentPair[1].length;

  // Get Stimuli
  // Define html strings for stimuli
  let stim_width_ft = "100px";
  const stim_html_strings_ft = []; 
  for (let i=0; i<nodePaths.length; i++) {
    stim_html_strings_ft.push(`<img src=${nodePaths[i]} style='max-width:${stim_width_ft};max-height:${stim_width_ft};'>`);
  }

  // Get dash
  const dash_width_ft = "50px";
  const dashStimHtml = `<img src=${dashPath} style='max-width:${dash_width_ft};max-height:${dash_width_ft};'>`;
  // Get flowers
  const path1Start = currentPair[0][0];
  const path1End = currentPair[0][currentPair[0].length-1];
  const path2Start = currentPair[1][0];
  const path2End = currentPair[1][currentPair[1].length-1];

  const choice1 = stim_html_strings_ft[path1Start] + dashStimHtml + stim_html_strings_ft[path1End];
  const choice2 = stim_html_strings_ft[path2End] + dashStimHtml + stim_html_strings_ft[path2Start];

  let choiceSwitched = null;

  const testingTrial = {
    type: jsPsychHtmlButtonResponse,
    required: true,
    stimulus: `
      <p>
        Please take your time and answer correctly: 
      </p>
      <p>
         Which route from start flower to end flower requires 
         <strong>less stopovers</strong> for the bee?
      </p>
    `,
    choices: function() {
      const choices = [choice1, choice2];
      const randChoices = randFlag ? jsPsych.randomization.shuffle(choices) : choices;
      choiceSwitched = randChoices[0]===choice1 ? false : true;
      return randChoices;
    },
    save_trial_parameters: {
      choices: true, // Save randomly-selected button order and post trial gap duration to trial data
      stimulus: true, // Save stimulus
    },
    on_finish: function(data) {
      // Score response as correct or incorrect and save
      if (choiceSwitched) {
        currentPair = currentPair.reverse()
        if (data.response == 0 && path1SDPlongerPath2) {
          data.correct = true;
        } else if (data.response == 1 && !path1SDPlongerPath2) {
          data.correct = true;
        } else {
          data.correct = false;
        }
      } else {
        if (data.response == 1 && path1SDPlongerPath2) {
          data.correct = true;
        } else if (data.response == 0 && !path1SDPlongerPath2) {
          data.correct = true;
        } else {
          data.correct = false;
        }
      }

      // Save data
      jsPsych.data.addDataToLastTrial({
        trial_name: "test_congr",
        trial_ind_congrtest: tTrialI,
        pathpair_congrtest: currentPair,
      });
    },
  };
  return testingTrial;
}

function createTestingInterTrial() {
  testingInterTrial = {
    type: jsPsychHtmlButtonResponse,
    stimulus: `
      `, 
    choices: ['Continue'],
    on_finish: function(data) {
      jsPsych.data.addDataToLastTrial({
        trial_name: "test_congr_inter",
      });
    },
  };
  return testingInterTrial;
}

function createTestingFeedback() {
  testingFeedback = {
    type: jsPsychHtmlButtonResponse,
    stimulus: function(){
      const last_trial_correct = jsPsych.data.get().last(1).values()[0].correct;
      if(last_trial_correct){
        return "<p>Correct!</p>";
      } else {
        return "<p>Wrong!</p>";
      }
    },
    choices: ['Continue'],
    on_finish: function(data) {
        jsPsych.data.addDataToLastTrial({
          trial_name: "test_congr_feedb",
      });
    },
  };
  return testingFeedback;
}

//}}}
// Testing: Spatial-positioning Instructions {{{

const spatialPosInstrTrial1 = {
  type: jsPsychHtmlButtonResponse,
  stimulus: itools.instrTask2Part2First,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "test_spatialpos_instr",
    });
  },
};


const spatialPosInstrTrial2 = {
  type: jsPsychHtmlButtonResponse,
  stimulus: itools.instrTask2Part2Sec,
  choices: ['Continue'],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "test_spatialpos_instr2",
      towPosLastTrial: jsPsych.data.get().last(2).values()[0].nodepos_spatialpos_norel,
    });

  },
};



// }}}
// Testing: Spatial-positioning Task {{{

function createSpatialPosTrial() {
  
  let saveNodePos = new Array();
  let trialEnded = false;

  let startTimeRT;
  let endTimeRT;

  const spatialpos_trial = {
    type: jsPsychP5JS,
    top_level_declarations: function (p){
      // Top Level Declarations ============================================== {{{
      p.TLD = {} // create an empty object tagged on p so the var's and funcs are accessible within setup and draw

      p.TLD.nbNodes = nbAllNodes;
      p.TLD.allPosRel = p.TLD.nbNodes*(p.TLD.nbNodes-1);

      // Create tower positions
      p.TLD.towPos = [];
      for (let i=0; i<p.TLD.nbNodes; i++) {
        let spacing = 70;
        p.TLD.towPos.push(
          [sizes["env"][0] + sizes["envExtra"]/2, 
           spacing/2 + spacing*i]
        );
      }

      // Define Nodes
      p.TLD.Node = class {
        constructor(x, y, diam, aspect, num=false) {
          this.x = x;
          this.y = y;
          this.diam = diam;
          this.aspect = aspect; // color or image
          this.num = num;
          this.msOver;
        }
        display() {
          if (typeof this.aspect == "string") {
            p.stroke("#000000");
            p.strokeWeight(1);
            p.fill(this.aspect);
            p.circle(this.x, this.y, this.diam);
          } else {
            p.image(this.aspect,
                    this.x - sizes["node"]/2, 
                    this.y - sizes["node"]/2,
                    sizes["node"],
                    sizes["node"],
            );
          }

          if (typeof this.num == "number") {
            p.textSize(18);
            p.textStyle("italic");
            p.fill("#000000");
            p.text(this.num.toString(), this.x, this.y);
           }  
        }
      }

      p.mousePressed = function () {
        for (i=0; i<p.TLD.nodes.length; i++) {
          // Check if cursor is at node
          if (p.dist(p.TLD.nodes[i].x, p.TLD.nodes[i].y, 
                     p.mouseX, p.mouseY) <= p.TLD.nodes[i].diam/2) {
            p.TLD.nodes[i].msOver = true;
            p.TLD.xOffset = p.mouseX - p.TLD.nodes[i].x;
            p.TLD.yOffset = p.mouseY - p.TLD.nodes[i].y;
          } else {
            p.TLD.nodes[i].msOver = false;
          }
        }
      }

      p.mouseDragged = function () {
        for (i=0; i<p.TLD.nodes.length; i++) {
          if (p.TLD.nodes[i].msOver) {
            // p.cursor(p.HAND);
            p.cursor(p.MOVE);
            p.TLD.nodes[i].x = p.mouseX - p.TLD.xOffset;
            p.TLD.nodes[i].y = p.mouseY - p.TLD.yOffset;
            break; // don't select more than one node simultaneously
          }
        }
      }

      p.mouseReleased = function () {
        p.cursor(p.ARROW);
      }

      p.mouseClicked = function () {
        for (let r of p.TLD.colorRels) {
          r.isHit(p.mouseX, p.mouseY);
        }
      }

      p.TLD.colorRels = [];
      p.TLD.colorRelation = class {
        constructor() {
          this.lineWidth = 16;
          this.active = false;
        }
        isHit(x, y) {
          let [mX, mY] = rotatePoint(
              [0, 0], [x-this.c1x-this.centerWidth, y-this.c1y], -this.lineAngle
          );
          let dist = 40;
          if (0 + dist <= mX && mX <= this.lineLength - dist
            && 0 <= mY && mY <= this.lineWidth) {
            // console.log("something hit me!");
            this.active = !this.active;
            return true;
          } else {
            return false;
          }
        }
        display(x1, y1, x2, y2, i, j) {

          if (x1 <= x2 && y1 <= y2) {
            this.c1x = x1;
            this.c1y = y1;
            this.c2x = x2;
            this.c2y = y2;
            this.centerWidth = this.lineWidth / 2;
          } else if (x1 > x2 && y1 <= y2) {
            this.c1x = x2;
            this.c1y = y2;
            this.c2x = x1;
            this.c2y = y1;
            this.centerWidth = - this.lineWidth ; 
          } else if (x1 <= x2 && y1 > y2) {
            this.c1x = x1;
            this.c1y = y1;
            this.c2x = x2;
            this.c2y = y2;
            this.centerWidth = -this.lineWidth / 2;
          } else { // x1 > x2 && y1 > y2
            this.c1x = x2;
            this.c1y = y2;
            this.c2x = x1;
            this.c2y = y1;
            this.centerWidth = this.lineWidth / 2;
          }
          this.lineLength = p.dist(this.c1x, this.c1y, this.c2x, this.c2y);
          this.lineAngle = getHorAngleFromLineSeg([this.c1x, this.c1y], 
                                                  [this.c2x, this.c2y]);
          p.push();
          if (this.active) {
            p.strokeWeight(8);
            p.stroke(colors["edgeTrue"])
          } else {
            p.strokeWeight(6);
            p.stroke(160, 160, 160, 127);
          }
          p.line(this.c1x, this.c1y, this.c2x, this.c2y);
          p.pop();
        }
      }

      p.TLD.drawRelations = function (adjMat, nodePos) {
        for (let i=0; i < nodePos.length; i++) {
          for (let j=0; j < nodePos.length; j++) {
            if (
              adjMat[i][j]==1 
                & p.TLD.mouseClicked
              ) {
              p.stroke(colors["edgeTrue"]);
              p.strokeWeight(2);
              p.line(nodePos[i][0], nodePos[i][1], 
                     nodePos[j][0], nodePos[j][1]);
              lineDist = false;
            } else {
              p.stroke("grey");
              p.strokeWeight(0.2);
            }
          }
        }
      }

      p.TLD.changeCursorHand = function (positions, thresh) {
        let dists = []
        for (const ps of positions) {
          dists.push(p.dist(p.mouseX, p.mouseY, ...ps));
        }
        if (dists.some(d => d < thresh)) {
          p.cursor(p.HAND);
        }
      }

      // }}}
    },
    setup_func: function(p) {
      // Set Up Function ===================================================== {{{

      p.TLD.colorRels = [];
      for (let i=0; i<p.TLD.allPosRel; i++) {
        p.TLD.colorRels.push(new p.TLD.colorRelation());
      }

      // Set up Background
      p.createCanvas(sizes["env"][0]+sizes["envExtra"], sizes["env"][1]);

      // Set up Nodes
      p.TLD.nodes = [];
      for (let i=0; i<p.TLD.towPos.length; i++) {
        let num = debugFlag ? i : false;
        let nodeObj = new p.TLD.Node(
          p.TLD.towPos[i][0],
          p.TLD.towPos[i][1],
          sizes["node"],
          p.loadImage(nodePathsSmall[i]),
          num=num,
        );
        p.TLD.nodes.push(nodeObj);
      }

      // }}}
     },
    draw_func: function(p){
      // Drawing Function ==================================================== {{{
      // Set Cursor
      p.cursor(p.ARROW);
      p.TLD.changeCursorHand(p.TLD.towPos, sizes["node"]/2);

      // Set Background
      p.background(colors["bgGreen"]);
      p.textSize(38);
      p.textFont('Courier New');
      p.fill(colors["envText"]);
      p.text('Arrange', 20, 40);

      // Draw Extra Background
      p.noStroke();
      p.fill(colors["bgWhite"]);
      p.rect(sizes["env"][0], 0, sizes["env"][0]+sizes["envExtra"], sizes["env"][1]);
      
      // Draw clickable relations between nodes
      if (type=="rel") {
        cRelI = 0;
        for (let i=0; i<p.TLD.nbNodes; i++) {
          for (let j=0; j<p.TLD.nbNodes; j++) {
            if (i<j) {
              p.TLD.colorRels[cRelI].display(
                p.TLD.towPos[i][0], p.TLD.towPos[i][1],
                p.TLD.towPos[j][0], p.TLD.towPos[j][1],
                i, j, // for saving the relation
              );
              cRelI++;
            } 
          }
        } 
      }

      // Draw nodes
      for (let i=0; i<p.TLD.nodes.length; i++) {
        p.TLD.nodes[i].display();
        p.TLD.towPos[i] = [p.TLD.nodes[i].x, p.TLD.nodes[i].y];
      }
      if (p.TLD.mouseClicked) {
        value = 0;
      } else {
        value = 255;
      }
      p.fill(value);

      // Save node positions
      saveNodePos = p.TLD.towPos;
      // Stop p5js animation
      if (trialEnded) p.remove(); 
      
      //}}}
    },
    on_start: function(data) {
      startTimeRT = performance.now();
    },
    on_finish: function(data) {
      trialEnded = true;
      endTimeRT = performance.now();
      const rt = endTimeRT-startTimeRT;
      data = {
        trial_name: "test_spatialpos_norel",
        nodepos_spatialpos_norel: saveNodePos,
        rt_spatialpos_norel: rt,
      }
      jsPsych.data.addDataToLastTrial(data);
    },
    key_choices: "NO_KEYS",
    button_choices: ['Continue'],
  };
  return spatialpos_trial;
}

// }}}
// Testing: Position-Drawing Task {{{

function createPosDrawTrial(c_type="first") {

  let trialEnded = false;
  let startTime = 100000000000;
  let nodeStarted = -1;
  let nodeEnded = -1;

  let connectedPos = [];
  let towPosLastTrial;

  let startTimeRT;
  let endTimeRT;

  const posDrawTrial = {
    type: jsPsychP5JS,
    top_level_declarations: function (p){
      // Top Level Declarations ============================================== {{{
      
      p.TLD = {} // create an empty object tagged on p so the var's and funcs are accessible within setup and draw

      // p.TLD.towPos = nodePos
      p.TLD.towPos = towPosLastTrial;
      p.TLD.nbNodes = p.TLD.towPos.length;

      // Define Nodes
      p.TLD.Node = class {
        constructor(x, y, diam, aspect, num=false) {
          this.x = x;
          this.y = y;
          this.diam = diam;
          this.aspect = aspect; // color or image
          this.num = num;
          this.msOver;
          this.msOverReleased = false;
        }
        display() {
          if (typeof this.aspect == "string") {
            p.stroke("#000000");
            p.strokeWeight(1);
            p.fill(this.aspect);
            p.circle(this.x, this.y, this.diam);
          } else {
            p.image(this.aspect,
                    this.x - sizes["node"]/2, 
                    this.y - sizes["node"]/2,
                    sizes["node"],
                    sizes["node"],
            );
          }
          if (typeof this.num == "number") {
            p.textSize(18);
            p.textStyle("italic");
            p.fill("#000000");
            p.text(this.num.toString(), this.x, this.y);
           }  
          
        }
      }

      p.TLD.changeCursorCross = function (positions, thresh) {
        let dists = []
        for (const ps of positions) {
          dists.push(p.dist(p.mouseX, p.mouseY, ...ps));
        }
        if (dists.some(d => d < thresh)) {
          p.cursor(p.CROSS);
        }
      }

      p.TLD.gridBackground = function(horLines=18, verLines=18) {
        for (let x = 0; x<sizes["env"][0]; x += sizes["env"][0]/verLines) {
          for (let y = 0; y<sizes["env"][0]; y += sizes["env"][0]/horLines) {
            p.stroke(colors["bgGrid"]);
            p.strokeWeight(0.5);
            p.line(x, 0, x, p.height);
            p.line(0, y, p.width, y);
          }
        }
      }

      p.mousePressed = function () {
        for (i=0; i<p.TLD.nodes.length; i++) {
          // Check if cursor is at node
          if (p.dist(p.TLD.nodes[i].x, p.TLD.nodes[i].y, 
                     p.mouseX, p.mouseY) <= p.TLD.nodes[i].diam/2) {
            p.TLD.nodes[i].msOverPressed = true;
          } else {
            p.TLD.nodes[i].msOverPressed = false;
          }
        }
      }

      p.mouseReleased = function () {
        for (i=0; i<p.TLD.nodes.length; i++) {
          // Check if cursor is at node
          if (p.dist(p.TLD.nodes[i].x, p.TLD.nodes[i].y, 
                     p.mouseX, p.mouseY) <= p.TLD.nodes[i].diam/2) {
            p.TLD.nodes[i].msOverReleased = true;
          } else {
            p.TLD.nodes[i].msOverReleased = false;
          }
        }
      }

      /** Checks if the mouse cursor is within a specified rectangular area, 
      * with optional padding. */
      p.TLD.isMsOver = function (posX, posY, widthX, widthY, padding=0) {
        let msOver = false;
        if ((posX-padding < p.mouseX) && (p.mouseX < posX+widthX+padding)
            && (posY-padding < p.mouseY) && (p.mouseY < posY+widthY+padding)
            ) {
          msOver = true;
        }
        return msOver;
      }

      /** Renders the background.*/
      p.TLD.renderBackground = function () {
        // Create background itself
        p.createCanvas(sizes["env"][0]+sizes["envExtra"], sizes["env"][1]);
        p.background(colors["bgGreen"]);
        p.TLD.gridBackground();
        p.textSize(38);
        p.textFont('Courier New');
        p.fill('grey');
        p.text('Draw', 20, 40);
        p.fill(colors["bgWhite"]);
        p.rect(sizes["env"][0], 0, sizes["env"][0]+sizes["envExtra"], sizes["env"][1]);
        p.image(p.TLD.undoButton, ...p.TLD.undoPos);
        // Control mouse over
        p.TLD.undoMsOver = p.TLD.isMsOver(...p.TLD.undoPos, padding=3)
      }

      /* Draw an edge between two points. */
      p.TLD.drawEdge = function(p1x, p1y, p2x, p2y) {
        p.stroke(colors["edgeUndef"]); // blue edge
        p.strokeWeight(6);
        p.line(p1x, p1y, p2x, p2y);
      }

      /* Check whether the cursor is near a line. */
      p.TLD.isCursorNearLine = function(x1, y1, x2, y2, dist, shorten=10) {
        // Shorten line by some amount
        [x1, y1, x2, y2] = htools.shortenLine(x1, y1, x2, y2, shorten);
        let px = p.mouseX;
        let py = p.mouseY;
        // Calculate the length of the line
        let lineLength = p.dist(x1, y1, x2, y2);
        // Project point onto line and clamp to the segment
        let t = ((px-x1)*(x2-x1)+(py-y1)*(y2-y1))/(lineLength*lineLength);
        t = p.constrain(t, 0, 1); // Clamp t to the range [0, 1]
        // Find the closest point on the line segment
        let closestX = x1 + t * (x2 - x1);
        let closestY = y1 + t * (y2 - y1);
        // Compute distance between the cursor and the closest point
        let d = p.dist(px, py, closestX, closestY);
        return d <= dist;
      }

      // }}}
    },
    setup_func: function(p) {
      // Set Up Function ===================================================== {{{

      // Set up Nodes
      p.TLD.nodes = [];
      for (let i=0; i<p.TLD.towPos.length; i++) {
        let num = (debugFlag | showNumFlag) ? i : false;
        let nodeObj = new p.TLD.Node(
          p.TLD.towPos[i][0], 
          p.TLD.towPos[i][1], 
          sizes["node"],
          p.loadImage(nodePathsSmall[i]),
          num=num,
        );
        p.TLD.nodes.push(nodeObj);
      }

      // Draw nodes
      p.noStroke();
      p.TLD.nodes.forEach(node => node.display());

      // Undobutton
      p.TLD.undoButton = p.loadImage(undoPath);
      p.TLD.undoPos = [
        sizes["env"][0]+sizes["envExtra"]-70, sizes["env"][1]-70, 50, 50
      ];

      // }}}
     },
    draw_func: function(p) {
      // Drawing Function ==================================================== {{{
      p.cursor(p.ARROW); // set cursor to arrow by default
      nodeEnded = -1; // necessary to be able to delete edges (one or all)

      let cursorHand = []
      for (const edge of connectedPos) {
        cursorHand.push(p.TLD.isCursorNearLine(...edge, 5));
      }
      cursorHand.push(p.TLD.undoMsOver);
      if (cursorHand.some(el => el === true)) p.cursor(p.HAND);

      // Run drawing over all nodes
      for (let i = 0; i < p.TLD.nodes.length; i++) {
        // Handle drawing and state changes when mouse is pressed over a node
        if (p.TLD.nodes[i].msOverPressed && p.mouseIsPressed) {
          p.cursor(p.CROSS);
          p.stroke(colors["drawStroke"]);
          p.strokeWeight(3);
          p.line(p.mouseX, p.mouseY, p.pmouseX, p.pmouseY);

          nodeStarted = i;
          nodeEnded = -1;

        // Handle state changes when mouse is released
        } else if (!p.mouseIsPressed) {
          // Set Background I
          p.TLD.renderBackground();
          for (const edge of connectedPos) {
            p.TLD.drawEdge(...edge);
          }

          // Delete drawing
          p.noStroke();
          p.TLD.nodes.forEach(node => node.display());
          p.TLD.changeCursorCross(p.TLD.towPos, sizes["node"]/2);

          // Determine if mouse was released over a node
          if (p.TLD.nodes[i].msOverReleased) {
            nodeEnded = i;
          }

          if (nodeStarted !== -1 
                && nodeEnded !== -1 
                && nodeStarted !== nodeEnded) {
            newEdge = [...p.TLD.towPos[nodeStarted], ...p.TLD.towPos[nodeEnded]];
            htools.addUniqueArray(connectedPos, newEdge);
          }
        }
      }

      // Determine click behavior
      // Delete one edge if line is clicked
      p.doubleClicked = function() {
        if (cursorHand.some(el => el===true)) {
        ind = cursorHand.findIndex(el => el===true);
        connectedPos.splice(ind, 1); 
        }
      }
      // Delete all edges if undo button is clicked
      if (p.mouseReleased && p.TLD.undoMsOver) connectedPos = [];

      // Calculate time
      elapsedTime = p.millis() - startTime;
      // Stop p5js animation
      if (trialEnded) p.remove(); 
          
      // }}}
    },
    on_start: function(trial) {
      console.log("c_type", c_type);
      if (c_type==="first") {
        towPosLastTrial = jsPsych.data.get().last(2).values()[0].nodepos_spatialpos_norel;
      } else {
        towPosLastTrial = jsPsych.data.get().last(1).values()[0].nodepos_spatialpos_norel;
        connectedPos = jsPsych.data.get().last(1).values()[0].connected_pos_spatialpos_rel;
        drawnRelations = jsPsych.data.get().last(1).values()[0].relations_spatialpos_rel;
      }
      startTimeRT = performance.now();
    },
    on_finish: function(data) {
      endTimeRT = performance.now();
      const rt = endTimeRT-startTimeRT;
      let drawnRelations = [];
      for (const rel of connectedPos) {
        let ind1 = towPosLastTrial.findIndex(
          nPos => JSON.stringify(nPos)===JSON.stringify(rel.slice(0,2))
        );
        let ind2 = towPosLastTrial.findIndex(
          nPos => JSON.stringify(nPos) === JSON.stringify(rel.slice(-2))
        );
        drawnRelations.push([ind1, ind2])
      }
      trialEnded = true;

      // Test connectedness of drawn graph
      const graphConnected = gtools.isConnected(
        gtools.transformToAdjacencyObject(towPosLastTrial.length, drawnRelations)
      );

      data = {
        trial_name: "test_spatialpos_rel",
        nodepos_spatialpos_norel: towPosLastTrial,
        connected_pos_spatialpos_rel: connectedPos,
        relations_spatialpos_rel: drawnRelations,
        rt_spatialpos_rel: rt,
        connected_spatialpos_rel: graphConnected,
      };
      jsPsych.data.addDataToLastTrial(data);
    },
    key_choices: "NO_KEYS",
    button_choices: ['Continue'],
    prompt: function() {
      let prpt;
      if (c_type==="first") {
        prpt = "Make sure the bee can reach each flower, i.e. no flower is disconnected.";
      } else {
        prpt = "Not all flowers are reachable for the bee. Please add one or more connections.";
      }
      return prpt
    },
  }
  return posDrawTrial;
}

function createCondPosDrawTrial() {
  const conditionalPosDrawTrial = {
    timeline: [createPosDrawTrial(c_type="conditional")],
    conditional_function: function() {
      // Access the last trial's data
      const graphConnected = jsPsych.data.get().last(1).values()[0]. connected_spatialpos_rel; 

      return !graphConnected; // Return true to show, false to skip
    },
  };
  return conditionalPosDrawTrial;
}

// }}}
// End Trials {{{

const cheater_trial = { // MAYDO: Do cheater trial after learning and after testing?
    type: jsPsychSurveyMultiChoice,
    questions: [
        {
            prompt: itools.instrCheater,
            name: "cheater",
            options: ["Yes", "No", "Sometimes"],
            required: !debugFlag,
        }
    ],
  on_finish: function(data) {
    jsPsych.data.addDataToLastTrial({
      trial_name: "cheater",
    });
  }
};


const finalTrialP1 = {
  type: jsPsychHtmlButtonResponse,
  stimulus: `<p>You have finished the last task of part I.</p> 
             <br>
            `,
  choices: ["Go to part II"],
}


function createFinalTrial(part=null) {
  let partInsert = "";
  let seeYou = "";
  if (typeof part == "number") {
    partInsert = ` of part ${part}`;
    if (part === 1) {
      seeYou = "That's enough for today, see you tomorrow. ";
    }
  }
  let finishButton = debugFlag ? ["Show data."] : [];

  const finalTrial = {
    type: jsPsychHtmlButtonResponse,
    stimulus: `<p>You've finished the last task${partInsert}.</p> 
              <h3>${seeYou}Thank you for participating!</h3>
               <br>
               <p>After 5 seconds, we redirect you automatically to prolific's completion URL.</p>
              `,
    trial_duration: 5000, // ms
    choices: finishButton,
    on_start: function() {
      // Send telegram message
      const telegramMsg = `${subject_id} part **${part}** finish.`;
      sendMessage(telegramMsg);
    },
    on_finish: function(data) {
      if (prolificFlag) window.location = prolif_compl_link; 
      jsPsych.data.addDataToLastTrial({
        trial_name: `final_learn_trial`,
      });
    }
  }

  return finalTrial;
}

//}}}
// Confidence Rating Trials {{{

function createConfidenceTrial(taskName, type="") {

  const confidenceRatingTrial = {
    type: jsPsychSurveyMultiChoice,
    questions: [
      {
        prompt: `Were the instructions clear or unclear to you?`,
        options: [
          "Fully clear",
          "Somewhat clear",
          "Somewhat unclear",
          "Fully unclear",
        ], 
        required: !debugFlag, 
        horizontal: false, 
        name: 'clarity'
      },
      {
        prompt: `Did you solve the task consciously 
                and deliberately, or unconsciously
                and intuitively?`,
        options: [
          "Fully conscious/deliberative", 
          "Fairly conscious/deliberative", 
          "Fairly intuitive/unconscious",
          "Fully intuitive/unconscious",
        ], 
        required: !debugFlag, 
        horizontal: false, 
        name: 'consciousness'
      },
      {
        prompt: `Did you find it easy or difficult to solve the task?`,
        options: [
          "Easy",
          "Quite easy",
          "Quite hard",
          "Hard",
        ], 
        required: !debugFlag, 
        horizontal: false, 
        name: 'difficulty'
      }, {
        prompt: `
          How confident are you that you solved the task correctly?
        `, 
        options: [
          "Confident",
          "Rather confident", 
          "Rather unconfident", 
          "Unconfident", 
        ], 
        required: !debugFlag, 
        horizontal: false, 
        name: `confidence`
      }
    ],
    preamble: "<h3>Task Evaluation</h3>",
    button_label: `Continue`,
    on_finish: function(data) {
      jsPsych.data.addDataToLastTrial({
        trial_name: `conf_ratings_${taskName}`,
        type_confratings: type,
      });
    }
  };
  return confidenceRatingTrial;
}

function createFreeEvalTrial(taskName, type="") {
  const freeEvalTrial = {
    type: jsPsychSurveyText,
    preamble: "<h3>Task Strategy</h3>",
    questions: [{
      prompt: `<p>Please take a minute and describe the strategy with 
               which you solved the last task.</p> 

              <p>Additionally&mdash;as we are still in the pilot phase&mdash;, we would be glad if you would use this field to inform us about anything that was unclear or possibly misleading to you.
              </p>`,
      name: "strategy",
      placeholder: "type your strategy here",
      columns: 75,
      rows: 7,
      required: false,
    }],
    on_finish: function(data) {
      jsPsych.data.addDataToLastTrial({
        trial_name: `freeeval_${taskName}`,
        type_freeeval: type,
      });
    },
  };
  return freeEvalTrial;
}

// }}}
// Additional Trials {{{

const thesisTrial = {
  // type: jsPsychHtmlKeyboardResponse,
  type: jsPsychHtmlButtonResponse,
  stimulus: `<div style="text-align: left;">
    <h1>Overview</h1>
    <p>Timon Kunze (SISSA), Mona Garvert (Maximilians-Uni Würzburg), Davide Crepaldi (SISSA)</p>
    <br>

    <h3>General Motivation</h3>
    <p>
    Is the structure of human knowledge representation <em>map-like and rather Euclidean</em>, or
    is it <em>graph-like and rather topological</em>?
    </p>
    <h3>Background</h3>
    <p>
    We call the two formats: <strong>cognitive maps</strong> and <strong>cognitive graphs</strong>:
    <ul>
    <li>Cognitive maps encode relations between embedded objects via <em>concrete angles and Euclidean distances</em></li>
    <li>Cognitive graphs encode relations via the <em>abstract connectivity structure</em> between objects. Variations in angles, Euclidean distances and other continuous transformations are meaningless.</li>

    </ul>
    
    </p>
    <h3>Online Experiment</h3>
    <h4>Specific Motivation</h4>
    <p>
    We aim to test if and under which conditions humans represent truly cognitive graphs. Do humans learn purely topological graphs that are invariant under
    continuous transformations if we vary the spatial presentation enough, or will they always
    be influenced by space in some way?
    </p>
    <h4>Experimental setup</h4>
    <p>
    We let <strong>five particpants groups</strong> to learn a graph consting of nodes and edges
    that is presented in a 2D environment (Fig.1). For each group, we progressively vary the 
    graph’s spatial presentation
    over learning trials. 
    <ol>
    <li>Group: we hold the presentation completely static;</li>  
    <li>Group: we rotate it only around its center; </li>
    <li>Group: we only vary node-to- node distances (equivalent to scaling); </li>
    <li>Group: we vary only angles between edges;</li>
    <li>Group: we vary the graph presentation completely unconstrained over the full environment. </li>
    </ol>
    <figure>
    <img src="./stimuli/other/ex_graph.png" alt="Example Graph" style="width:900px;height:450px;">
    <figcaption>Fig.1 The graph as it is presented to the particpants in a 2d environment. 
    The nodes of the graph are flowers (left).
    Connecting edges have to be memorized by the participant (right) by watching a bee flying from one flower
    to another (not depicted).</figcaption>
    </figure>
    <h4>Prediction</h4>
    <p>
    We predict that participants represent relational knowledge in a map-like 
    format if we hold the presentation constant,
    but represent it in a graph-like format if we vary the presentation a lot.
    The influence of space should progressively weaken as a function
    of how strongly we vary the graph. 
    </p>

    <h4>Behavioral Signature</h4>
    <p>
    Participants are tested whether shorter Euclidean distances in the presentation facilitate
    decision making and whether longer Euclidean distances impede it.
    In the task participants are given a <strong>pair of paths</strong> and are asked to judge for which one of the paths the <em>shortest path distance (SPD)</em> on the graph is shorter.  
    </p>
    <p>
    We measure a <strong>congruency effect</strong> and predict less accuracy and longer reaction times for incongruent paths:
    </p>
    <ul>
    <li><strong>Congruent paths</strong>: If SPD from A to B is smaller than from C to D, <em>and</em> Eucliean Distance is <em>also</em> smaller for A to B compared to C to D</li>
    <li><strong>Incongruent paths</strong>: If SPD from A to B is smaller than from C to D, <em>but</em> Eucliean Distance is larger for A to B compared to C to D</li>
    </ul>
    <p>
    </p>
    <h3>Outlook</h3>
    <p>
    If the experiments is successful, we plan to analyze the neural representation of cognitive maps and graphs via fMRI adaptation (Barron et al., 2016).
    </p>
    <h3>References</h3>
    <ul>
    <li>Barron, H. C., Garvert, M. M., & Behrens, T. E. J. (2016). Repetition suppression:
    A means to index neural representations using BOLD? Philosophical Transactions of 
    the Royal Society B: Biological Sciences, 371(1705), 20150355. https://doi.org/10.1098/rstb.2015.0355</li>
    </ul>
    <p>
    </p>


    </div>
    `,
  choices: ['Continue'],
}

// }}}
// Timeline Functions {{{

/* Create Learning Trials */
function createLearnTrials(
  nbLearnPasses, debugFlag, nodePoss, relations,
  varType="rotational", type,
) {

  learnTrialsTL = [];
  let randAngle = 0;
  const nbRelations = relations.length; 
  // let learnTrialsCount = 0;

  let learnPassI;
  for (learnPassI=0; learnPassI<nbLearnPasses; learnPassI++) {
    for (let trialI = 0; trialI < nbRelations; trialI++) {
      nodePosInd = learnPassI*nbRelations + trialI*2;
      // console.log("learnPassI", learnPassI)

      // Create random angle
      if (varType=="rotational") {
        randAngle = Math.random() * Math.PI * 2; // Get random float between 0 and 2pi
        nodePos = Array(nodePoss[0].length);
        for (let i=0; i<nbAllNodes; i++) {
          nodePos[i] = rotatePoint(
            [sizes["env"][0]/2, sizes["env"][1]/2], nodePoss[0][i], randAngle,
          );
        }
      } else {
        nodePos = nodePoss[nodePosInd];
      }
      // Create learning environment trial
      const learnTrialAnim = createLearnTrialAnim(
        nodePos, relations, trialI, rotAngle=randAngle);
      learnTrialsTL.push(learnTrialAnim);

      // Create new random angle
      if (varType=="rotational") {
        randAngle = Math.random()* Math.PI*2; // Get random float between 0 and 2pi
        nodePos = Array(nodePoss[0].length);
        for (let i=0; i<nbAllNodes; i++) {
          nodePos[i] = rotatePoint(
            [sizes["env"][0]/2, sizes["env"][1]/2], nodePoss[0][i], randAngle,
          );
        }
      } else {
        nodePos = nodePoss[nodePosInd+1];
      }
      // Create drawing environment trial
      const drawingTrial = createDrawingTrial(
        nodePos=nodePos, rel=relations[trialI], 
        trialI=trialI, learnPassI=learnPassI, andle=randAngle, type=type);
      learnTrialsTL.push(drawingTrial);
    }
  }
  const drawingSummary = createDrawingTrialSummary(
    trlsBack=learnTrialsBlock*2, block=type);
  learnTrialsTL.push(drawingSummary);

  return learnTrialsTL;
}


/* Create relation-query trials (learn final) */
function relQueryTrials(testPasses, feedback=false, randF, adjMat, type) {
  let relQueryTL = [];

  // Get relations and shuffle randomly
  let relations = getRelations(adjMat, 1, true);
  // Get non relations and shuffle randomly
  let nonRelations = getRelations(adjMat, 0, true);
  const nbQueryTrials = nbRelations*testPasses*2;
  let randBinListQuery;
  if (randF) {
    relations = htools.shuffleArray(relations);
    nonRelations = htools.shuffleArray(nonRelations);
    randBinListQuery = htools.generateRandomBinaryList(nbRelations);
  } else {
    const ones = Array.from({ length: nbRelations }, () => 1);
    const zeros = Array.from({ length: nbRelations }, () => 0);
    randBinListQuery = ones.concat(zeros), type;
  }

  let relI = 0;
  let nonRelI = 0;
  for (let i=0; i<nbQueryTrials; i++) {
    if (randBinListQuery[i]===1) {
      learnTrialRelQuery = createLearnTrialRelQuery(relations[relI], 1, i, type);
      relI++;
    } else {
      learnTrialRelQuery = createLearnTrialRelQuery(nonRelations[nonRelI],0, i, type);
      nonRelI++;
    }
    relQueryTL.push(learnTrialRelQuery);
    if (feedback) {
      relQueryTL.push(createLearnTrialFeedback());
    }
  }
  return relQueryTL;
}

// }}}
// Build Timeline {{{

// Define Timelines
// ================
let coreTimeline = [];
let learnTimeline = [];
let testTimeline = [];


// Part 0: Create coreTimeline
// ============================

// coreTimeline.push(thesisTrial);
coreTimeline.push(preload_trial);
coreTimeline.push(welcome_trial);
coreTimeline.push(consent_trial);
coreTimeline.push(fullscreen_trial);

// Part 1: Create learnTimeline
// ============================

// Consent, Age and Gender
// -----------------------
let learnIntroTimeline = [];
learnIntroTimeline.push(age_trial);
learnIntroTimeline.push(gender_trial);

// Learning Instructions
// -----------------------
learnIntroTimeline.push(learnInstrTrial);

// Learning: Sample
// ----------------
let learnPassI = null;
for (let trialI = 0; trialI < sampleRels.length; trialI++) {
  const sampleTrialAnim = createLearnTrialAnim(
    sampleNodePos, sampleRels, trialI, learnPassI, type="sample");
  learnIntroTimeline.push(sampleTrialAnim);

  const sampleDrawingTrial = createDrawingTrial(
    nodePos=sampleNodePos, rel=sampleRels[trialI], trialI=trialI, 
    learnPassI=null, angle=0, type="sample");
  learnIntroTimeline.push(sampleDrawingTrial);
}
learnIntroTimeline.push(
  createDrawingTrialSummary(trlsBack=sampleRels.length*2, block="sample"))
learnIntroTimeline.push(learnInstrEndTrial);

// Learning Blocks
// ---------------
const blocks = ["first", "second", "third", "fourth", "fifth", "sixth"];
for (let blockI = 0; blockI < nbLearnBlocks; blockI++) {
  block = blocks[blockI];
  learnTimeline.push(...createLearnTrials(
    nbLearnPasses, debugFlag, allNodePoss, relations, varType, type=block,
  ));
  if (block === "first") {  // Don't use these conf-trials in part1 anymore.
    learnTimeline.push(learnTrialRelQueryInstr);
  }
  learnTimeline.push(...relQueryTrials(testPasses=1, feedback=false, 
                                       randF=randFlag, adjMat=adjMat, type=block));
  if (feedbackFlag) {
    learnTimeline.push(createRelQueryTrialFeedback(testPasses=1));
  }
}

// Part I Final
// ------------
if (part1Flag == true && part2Flag == true) {
  learnTimeline.push(finalTrialP1);
} else {
  learnTimeline.push(createFinalTrial(part=1));
}


// Part II: Create testTimeline
// ============================

// Instructions 3 (Congr Test)
// ---------------------------
if (debugFlag) {
  testTimeline.push(
    createLearnTrialAnim(allNodePoss, relations, trialI=0, learnPassI, rotAngle=0)
  );
}
testTimeline.push(testOneInstrTrial1);
testTimeline.push(testOneInstrTrial2);

// Task 3 (Congr Task)
// ------------------
for (let tTrialI=0; tTrialI<test3Pairs.length; tTrialI++) {
  currentPair = test3Pairs[tTrialI];
  testTimeline.push(createCongrTestTrial(tTrialI, currentPair, randFlag));
}
testTimeline.push(createConfidenceTrial("congrtest"));
testTimeline.push(createFreeEvalTrial("congrtest"));

// Instruction 4 & Task 4 (Spatialpos)
// -----------------------------------
testTimeline.push(spatialPosInstrTrial1);
testTimeline.push(createSpatialPosTrial());
testTimeline.push(spatialPosInstrTrial2);
let task4bConnected = false;
testTimeline.push(createPosDrawTrial("first"));
for (let i=0; i<5; i++) {
  testTimeline.push(createCondPosDrawTrial());
}
testTimeline.push(createConfidenceTrial("spatialpos"));
testTimeline.push(createFreeEvalTrial("spatialpos"));

// Cheater & Final
// ---------------
testTimeline.push(cheater_trial);
testTimeline.push(createFinalTrial(part=2));


// Build Full Timeline
// ====================
let fullTimeline = [];

if (!staticFlag) {
  // Create normal timeline
  fullTimeline.push(...coreTimeline);
  if (part1Flag) {
    fullTimeline.push(...learnIntroTimeline);
    fullTimeline.push(...learnTimeline);
  } 
  if (part2Flag) {
    fullTimeline.push(...testTimeline);
  }
} else {
  // Create static timeline (for screenshots)
  randFlag = false;
  const nP = allNodePoss.slice(0, 40);
  const nR = relations.slice(5,8);
  console.log(nP.length)
  console.log(nP)
  fullTimeline.push(...createLearnTrials(
    1, debugFlag, nP, nR, varType, type=block,
  ));
  fullTimeline.push(...relQueryTrials(testPasses=1, feedback=false, 
                                       randF=randFlag, adjMat=adjMat, type=block));
}
jsPsych.run(fullTimeline);

// }}}
