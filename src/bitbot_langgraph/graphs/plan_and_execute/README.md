from: https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/
also (paper): https://arxiv.org/abs/2305.04091


A good run:
https://smith.langchain.com/o/95ef8075-73f1-56a8-bdb2-43d8815e68b8/projects/p/3d787172-5b2f-4a11-a4d0-49a93a1833c1?timeModel=%7B%22duration%22%3A%221h%22%7D&peek=db70d958-c05e-4045-a366-50f387310c03

key reasons
- verbose, detailed question
- gpt-4o (not gpt-4o-mini) for planning
- make sure agent has context


```


# old stuff we might use later


# # [{"url": url, "title": title, "description": description, "content": content}]
# # class ResearchItem(BaseModel):
# #     url: str
# #     title: str
# #     description: str
# #     content: str

# # class ResearchItems(BaseModel):
# #     items: list[ResearchItem]


# # lesson structure
# class Lesson(BaseModel):
#     title: str
#     content: str
    
# lesson_structure = """
# # Lesson: [title. example: OOPs! Introduction to the Order of Operations in mathematics]

# **Duration:** [duration. example: 30 minutes]

# ---

# # Objective:
# [objective. example: Understand and apply the order of precedence for mathematical operators in expressions.]

# ---

# # Materials Needed:
# - [list of materials needed. example: Whiteboard, chalkboard, or paper]
# - [additional materials. example: Calculator (optional, for checking answers)]

# ---

# # Lesson Outline:
# 1. **[Introduction to Topic]** ([time duration. example: 5 minutes])
# 2. **[Key Concept or Rule Introduction]** ([time duration. example: 10 minutes])
# [...etc...]

# ## 1. [Introduction to Topic] ([time duration. example: 5 minutes])

# ### [Subtopic 1 - Definition or Concept Introduction]
# [paragraph explaining the first subtopic. example: Operators are symbols that represent mathematical operations such as addition (+), subtraction (-), multiplication (×), division (÷), and exponentiation (^).]

# [additional paragraphs or explanations related to the first subtopic.]

# ### [Subtopic 2 - Importance or Application]
# [paragraph explaining the importance or application of the topic. example: The order in which operations are performed significantly affects the outcome of mathematical expressions.]

# [additional paragraphs or explanations related to the importance or application.]

# ## 2. [Key Concept or Rule Introduction] ([time duration. example: 10 minutes])

# ### [Subtopic 1 - Specific Rule or Principle]
# [paragraph introducing the specific rule or principle. example: In mathematics, not all operations are treated equally; some must be performed before others according to specific rules.]

# [additional paragraphs or explanations related to the specific rule or principle.]

# ### 1. [First Element of the Rule or Principle]
# [explanation of the first element. example: Parentheses are used to group parts of an expression that should be evaluated first.]

# #### Examples:
# - [Example 1]
# - [Example 2]
# [...additional examples as needed...]

# ### 2. [Next Element of the Rule or Principle]
# [explanation of the next element. example: Exponents are calculated after parentheses and before multiplication, division, addition, or subtraction.]

# [...continue with other elements...]

# ## [Next Major Section...]
# [Continue outlining the rest of the lesson in a similar format.]

# ---

# # Conclusion:
# [summary of the lesson. example: now you know...]
# """

# lesson_converter_prompt = """
# For the given messages & research items, Output a lesson in markdown format.
# The lesson should focus on a homeschool environment in which there are only a couple of children (siblings) of different ages.
# Do not suggest breaking up in groups. be thorough when providing examples.  Provide at least 3 more than you think you should.
# Here are the messages:
# {messages}

# Here are the research items:
# {research_items}

# The lesson should be structured as follows:
# {lesson_structure}
# """
# def make_lesson_message_converter(prompt_str=lesson_converter_prompt):
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             (
#                 "system",
#                 prompt_str
#             ),
#             ("placeholder", "{messages}"),
#             ("placeholder", "{research_items}"),
#             ("placeholder", "{lesson_structure}"),
#         ]
#     )
#     return prompt | ChatOpenAI(
#         model="gpt-4o", temperature=0
#     ).with_structured_output(Lesson)

# file_structure_example = """
# /app/docs_root/
#     curriculum/
#         mathematics/
#             grade_1/
#                 addition/
#                     index.md
#                     properties.md
#                     single_digit.md
#                     double_digit.md
#                     many_digits.md
#                     [...etc...]
#                 subtraction/
#                     index.md
#                     properties.md
#                     single_digit.md
#                     double_digit.md
#                     many_digits.md
#                     [...etc...]
#                 [...etc...]
#             [...etc...]
#         social_studies/
#             grade_1/
#                 geography/
#                     index.md
#                     maps.md
#                     globes.md
#                     [...etc...]
#                 history/
#                     index.md
#                     ancient_civilizations.md
#                     modern_era.md
#                     [...etc...]
#                 [...etc...]
#             [...etc...]
#         [...etc...]   
# """
# # the template is:
# # /app/docs_root/curriculum/{subject}/{grade}/{topic}/{document}.md

# # This will be run before each worker agent begins work
# # It makes it so they are more aware of the current state
# # of the working directory.
# def prelude(state):
#     # get working directory from env
#     WORKING_DIRECTORY_ENV = os.getenv("WORKING_DIRECTORY", "/app/docs_root")
#     WORKING_DIRECTORY = Path(WORKING_DIRECTORY_ENV)

#     written_files = []
#     if not WORKING_DIRECTORY.exists():
#         WORKING_DIRECTORY.mkdir()
#     try:
#         written_files = [
#             f.relative_to(WORKING_DIRECTORY) for f in WORKING_DIRECTORY.rglob("*")
#         ]
#     except Exception:
#         pass
#     if not written_files:
#         return {**state, "current_files": "No files written."}
#     return {
#         **state,
#         "current_files": "\nBelow are files your team has written to the directory:\n"
#         + "\n".join([f" - {f}" for f in written_files])
#         + "\nHere is an example of the file structure:\n"
#         + file_structure_example
#         + "\n"
#         + "respect the format indicated by the following examples:"
#         + "\n"
#         + "- /app/docs_root/curriculum/[subject]/[grade]/[topic]/[document].md"
#         + "\n"
#         + "- /app/docs_root/curriculum/[subject]/[grade]/[topic]/[graph_title].png"
#         + "\n"
#         + "\n"
#         + "generate meaningful names for [document] and [graph_title] to make it easier for humans to navigate the files."
#         + "\n"
#         + "Do not include spaces or special characters in file names. Use only letters, numbers, underscores, and hyphens."
#         + "\n"
#         + "For example, use 'grade_1' instead of 'Grade 1'.",
#     }

```