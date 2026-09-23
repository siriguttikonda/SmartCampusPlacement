/* =========================================================
   SMART CAMPUS
   GLOBAL JAVASCRIPT
   ========================================================= */


/* =========================================================
   SKILL AUTOCOMPLETE
   ========================================================= */

const availableSkills = [
    "Python",
    "Java",
    "C",
    "C++",
    "JavaScript",
    "HTML",
    "CSS",
    "MySQL",
    "MongoDB",
    "Flask",
    "Django",
    "Git",
    "Data Structures",
    "Machine Learning",
    "Artificial Intelligence",
    "Data Analysis",
    "React",
    "Node.js"
];


const skillInput =
    document.getElementById("skillInput");


const suggestionsBox =
    document.getElementById("suggestions");


if (skillInput && suggestionsBox) {

    skillInput.addEventListener(
        "input",
        function () {

            const input =
                skillInput.value
                    .trim()
                    .toLowerCase();


            suggestionsBox.innerHTML = "";


            if (!input) {

                suggestionsBox.style.display =
                    "none";

                return;

            }


            const matches =
                availableSkills.filter(
                    function (skill) {

                        return skill
                            .toLowerCase()
                            .includes(input);

                    }
                );


            if (matches.length === 0) {

                suggestionsBox.style.display =
                    "none";

                return;

            }


            matches.forEach(
                function (skill) {

                    const div =
                        document.createElement("div");


                    div.className =
                        "suggestion";


                    div.textContent =
                        skill;


                    div.addEventListener(
                        "click",
                        function () {

                            skillInput.value =
                                skill;

                            suggestionsBox.innerHTML =
                                "";

                            suggestionsBox.style.display =
                                "none";

                        }
                    );


                    suggestionsBox.appendChild(
                        div
                    );

                }
            );


            suggestionsBox.style.display =
                "block";

        }
    );

}


/* =========================================================
   ADD SKILL
   ========================================================= */

function addSkill() {

    if (!skillInput) {
        return;
    }


    const skill =
        skillInput.value.trim();


    if (skill === "") {

        skillInput.focus();

        return;

    }


    const form =
        document.createElement("form");


    form.method =
        "POST";


    const hiddenInput =
        document.createElement("input");


    hiddenInput.type =
        "hidden";


    hiddenInput.name =
        "skill_name";


    hiddenInput.value =
        skill;


    form.appendChild(
        hiddenInput
    );


    document.body.appendChild(
        form
    );


    form.submit();

}