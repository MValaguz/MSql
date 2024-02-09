class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def allPathsSourceTarget(graph):
    def dfs(node, path):
        if node == len(graph) - 1:
            res.append(path)
        else:
            for nei in graph[node]:
                dfs(nei, path + [nei])

    res = []
    dfs(0, [0])
    return res

root = TreeNode(1)
root.left = TreeNode(2)
root.right = TreeNode(3)
root.left.left = TreeNode(4)
root.left.right = TreeNode(5)
root.right.left = TreeNode(6)
root.right.right = TreeNode(7)

graph = {i: [] for i in range(8)}
for i in range(8):
    if root.left and root.left.val == i:
        graph[i].append(i + 1)
        graph[i].append(i + 2)
    elif root.right and root.right.val == i:
        graph[i].append(i + 1)
        graph[i].append(i + 2)
    elif i < 7:
        graph[i].append(i + 1)

print(graph)        

print(allPathsSourceTarget(graph))