import sys
import time
from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # 对于每个填字游戏的单词
        for x in self.crossword.words:
            # 遍历所有填字游戏的变量
            for v in self.domains.keys():
                # 如果单词的长度与变量的长度不一致
                if len(x) != v.length:
                    # 从变量的域中删除此单词
                    self.domains[v].remove(x)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # 获取变量`x`和`y`的重叠位置
        loc = self.crossword.overlaps[x, y]
        remove_words = []  # 用于存储要从`self.domains[x]`中删除的单词
        if loc != None:
            i, j = loc
            revised = False
            # 对于`x`的每个单词
            for word in self.domains[x]:
                flag = True
                # 对于`y`的每个单词
                for candi in self.domains[y]:
                    # 如果在重叠位置字符匹配
                    if word[i] == candi[j]:
                        flag = False
                        break
                if flag:
                    # 如果没有匹配的字符，将该单词添加到删除列表中，并标记为已修订
                    remove_words.append(word)
                    revised = True
            # 从`self.domains[x]`中删除不一致的单词
            for w in remove_words:
                self.domains[x].remove(w)
            return revised  # 返回是否进行了修订
        return False

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs == None:
            arcs = []
            # 生成所有可能的变量
            for v1 in self.domains.keys():
                for v2 in self.domains.keys():
                    if v1 != v2:
                        arcs.append((v1, v2))
        while len(arcs) > 0:
            x, y = arcs[0]
            arcs = arcs[1:]
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for v in self.crossword.neighbors(x):
                    arcs.append((v, x))
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return len(assignment) == len(self.domains) # 检查assignment中的变量数量是否与总变量数量相等


    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # 检查单词是否适合填字游戏
        for v, word in assignment.items():
            if v.length != len(word):
                return False

        # 检查分配值是否不同
        if len(assignment) != len(set(assignment.values())):
            return False

        # 检查是否存在冲突字符
        for var_pair, loc in self.crossword.overlaps.items():
            if loc != None:
                x, y = var_pair
                i, j = loc
                if x in assignment and y in assignment and assignment[x][i] != assignment[y][j]:
                    return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        return list(self.domains[var]) # 返回变量的列表

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned = set(self.domains.keys()) - set(assignment.keys())
        return list(unassigned)[0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # 如果分配已经完成（所有变量都已经分配了单词），则返回分配结果
        if self.assignment_complete(assignment):
            return assignment
        # 获取未分配变量的域值列表，按照某种顺序排列，通常是根据约束来排序
        unassigned_var = self.select_unassigned_variable(assignment)
        domain = self.order_domain_values(unassigned_var, assignment)
        for word in domain:
            # 复制当前分配，以便在尝试不同值时保持原始分配的不变性
            new_assignment = assignment.copy()
            new_assignment[unassigned_var] = word
            # 检查新分配是否与当前约束一致
            if self.consistent(new_assignment):
                result = self.backtrack(new_assignment)
                if result != None:
                    return result
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    start = time.time() # 记录开始时间
    assignment = creator.solve()
    end = time.time()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        print("Time :", end-start)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()