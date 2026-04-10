// helper-tools.js

const itools = (function() {
  // Store public functions and variables
  let public = {};

  public.instrTask1Part1 = `
    <h1>Part I</h1>
    <br>
    <h2>Task 1</h2>
    <h3>Instructions</h3>
    <p>
      In this task, you will see several flowers on a meadow. Your task is to <strong>find a hidden bee</strong> by clicking on the flowers. When you have found the bee, observe from which flower the bee flies to which other flower and remember this.
    </p>
    <p>
      Next, we ask you to <strong>draw the bee's flight path</strong> by clicking on one flower and dragging the cursor to another flower. This creates a connection between the two flowers, and a green or red line indicates whether the connection is correct. Only if your drawing was correct, or if you have drawn more than 10 incorrect connections,  can you move on to the next trial. Please be aware that during this task the position of the flowers on the meadow may change from time to time, but this should not hinder you in drawing the correct connection.
    </p>
    <p>
      Note that, firstly, the direction in which you see the bee flying does not matter, because for every direction in which you see a bee flying, we will also present you with the opposite direction. Similarly, it doesn't matter in which direction you draw the connection.
    </p>
    <p>
      Periodically give you a performance score based on your first-attempt accuracy over multiple trials. 
    </p>
    <p>
      Before starting, you can try <strong>two example trials</strong> by clicking 'Continue.'
    </p>
    `;

  public.instrTask1Part1End = `
    <h3>Are you ready?</h3>
    <br>
    <p>The testing phase is over. As said before, the task is to remember start and end position of the bee in each trial. 
    </p>
    <p> If you are ready you can click on the 'Continue' button, and the experiment begins.
    </p>
    `;


  let stim_width_ex = "600px";

  public.instrTask2Part1 = `
    <h2>Task 2</h2>
    <h3>Instructions</h3>
    <p>
      Did you notice that the bee only flew between certain pairs of flowers and not between others? We call the former <strong>&ldquo;known pairs&rdquo;</strong> and the latter <strong>&ldquo;unknown pairs&rdquo;</strong>. You may also have noticed that if the bee knew a connection, it flew equally in both directions, as such the directionality is not important..
    </p>
    <p>
      In the following, we show you several pairs of flowers, and please try to remember from the previous task <strong>whether the bee knows or does not know the shown flower pair</strong>.
    </p>
    <p>
      Indicate your answer with a button click. The task looks like this:
    </p>
    <p>
      <img src="./stimuli/other/reltest_example.png" style='max-width:${stim_width_ex};max-height:${stim_width_ex};'>
    </p>
    <p>
      This time, you don't need a test trial. Go right ahead.
    </p>
   `;

  public.instrTask1Part2 = `
    <h1>Part II</h1>
    <br>
    <h2>Task 1</h2>
    <h3>Instructions</h3>
    <p>
      In yesterday's part of the experiment, you have learned that the bee only flies between certain known pairs of flowers and does not fly between other, unknown pairs of flowers.
    </p>
    <p>
      Today we ask you to help the bee fly between flowers whose connections are not known. In order to do so, the bee will need to go from one flower to the next <strong>indirectly</strong> via the <strong>known connections from yesterday</strong>. 
    </p>
    <p>
      Note, however, that the bee must make a stopover when passing flowers via known connections, and each of these stopovers takes time. It is therefore important that the bee finds out which route has the <strong>fewest stopovers</strong>.
    </p>
    <p>
      In the following, we like to ask you to take over this task for the bee... 
    </p>
    <br>
    `;

  public.instrTask2Part2First = `
    <h2>Task 2</h2>
    <h3>Instructions</h3>
    <br>
    <p>In the next part of the experiment we ask you to <strong>position the flowers on the meadow</strong> in a way that seems reasonable to you.
    </p>
    <p>
    To begin with, the flowers are placed on the right-hand side. To place a flower on the meadow, click on the flower and drag it to a place you think fits best. Note that you can adjust the positions by dragging and droping flowers multiple times.
    </p>
    <p>There is no test attempt since you will figure it out easily. Take as much time as you like.
    </p>
    <br>
    `; 

  public.instrTask2Part2Sec = `
    <h3>Instructions</h3>
    <p>
      Next, we show you the meadow with the flowers as you positioned them before. But this time we ask you to <strong>draw in the known connections</strong> as you remember them.
    </p>
    <p>
      You can draw connections as before by <strong>dragging and dropping</strong> the cursor from one flower to another. If you want to delete an already drawn connection you can <strong>double-click</strong> on it, or you click on the <strong>reset button</strong> that deletes all previosly drawn connection in one go.
    </p>
    <p>
      Please make sure that the bee can reach all flowers by at least one connection.
    </p>
    <p>
    There's no time limit. Take your time and click on 'Continue' once you are done.
    </p>
    <br>
    `; 


  public.instrCheater = `
    <h3>Congratulations, you are nearly done. One last question:</h3>
    <br>
    <p>
    Did you use any means of documentation for learning the bee's connections in part 1, or for solving the task in part 2 (e.g. by writing down the connections)? 
    </p>
    <p>
    (Please be honest and note that your answer to this question will not affect your payment in any way.)
    </p>
  `;

  return public;
})();
