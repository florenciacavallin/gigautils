# giga-utils
#### This submodule contains utilities common to the SaaS, energy-trade, and grids repositories.
The main purpose of this repository is to serve as a third-party tool used by all three repositories to manage certain tasks.
When implemented correctly, it should reduce duplicated code and standardize processes such as authentication, database management, parameter validation, and other potential tasks.
## Guide to using submodules
### Creating a submodule in an existing project
1. Create your submodule: To create a submodule, you first need to create a repository that will eventually serve as the submodule of another repository. All submodules are actually repositories that are considered submodules of another one.
2. Add the new repository to the repository that will use it as a submodule: This is as easy as typing git submodule add https://github.com/florenciacavallin/giga-utils.git. Once this is done, a new directory named giga-utils will be created in your main repository.
3. Type git status and you will see that a .gitmodules file was created. It should look something like this:
```
[submodule "giga-utils"]
path = giga-utils
url = https://github.com/florenciacavallin/giga-utils.git
```
If you have multiple submodules, they should be shown here.
If you want to remove a submodule, you should delete it here.
### Initializing a project with submodules
When you clone a repository with submodules in it, by default you get the directories that contain submodules, but they are empty.
1. You will need to run ```git submodule init``` to initialize the submodules.
2. Then run ```git submodule update``` to fetch all the data from that project.
3. If you have many submodules in the project and would like these two steps to be done automatically, you can add the flag ```--recurse-submodules``` when you clone the repository.
4. You can combine ```git submodule init``` and ```git submodule update``` by running ```git submodule update --init```.
5. To initialize, fetch, and check out any nested submodules, you can run ```git submodule update --init --recursive```.
### Working with submodules
1. If you just want to check for updates in the submodule, you should run ```git fetch```.
2. If you want your repository to use the most up-to-date version of the submodule, you should run ```git merge```.
3. If you want these two steps to be done automatically for all your submodules, you should run ```git submodule update --remote``` (this will take the default branch of all submodules).
4. When you are working on a project and make changes to both the project and its submodule, you need to push your changes to both. One way to ensure this is to run ```git push --recurse-submodules=[check, on-demand]``` or to cd into the submodule and run ```git push```.

For more information, visit the [git submodules documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules).
