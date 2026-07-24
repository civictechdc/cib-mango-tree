# Profiling

In order to improve the performance of an application, it is necessary to understand what it is currently doing, and what parts of the application are taking time and computing resources.

There are many tools available to profile a Python application. Three of the most widely used are cProfile and samply. There are also many tools available for visualizing the output of profilers. For cProfile output, the snakeviz visualizer works well, while samply uses the Firefox profiler (included in many browsers other than Firefox).


## Profiling with samply

For GUI apps like CIB Mango Tree, which will be using multiple processes by default, `samply` should be your first choice, as it will sample over all those processes and the threads they spawn. Instructions on how to install `samply` can be found [here](https://github.com/mstange/samply).

Using samply is as easy as running `samply record ./my_application my_arguments` from the command line. For CIB Mango Tree, that would be:

```
samply record cibmt
```

Running this command will launch the CIB Mango Tree application as normal. 

### Exploring samply output in the browser

Once the application closes, samply will save a compressed profile, by default named profile.json.gz to disk, and will then open it in the default browser using the Firefox profiler. Many browsers already bundle it, but you may need to download it separately. This will provide a great deal of in-depth information on the number and lifespan of processes, threads, and which functions dominate runtime in each of them.

However, the output of `samply` can be overwhelming and difficult to interpret.

## Profiling with cProfile

For simpler profiling, `cProfile` is often preferred. However, note that `cProfile` will not effectively profile multiple processes, and it does not follow function calls across FFI boundaries.

Using `cProfile` is also simple. If your computer has Python installed, it should also have cProfile, as it's bundled with the Python interpreter. You can use it as:  

```
python3 -m cProfile -o profile_name.prof /.my_program.py my_arguments
```

cProfile works best when profiling Python scripts directly, rather than GUI applications. If possible, extract your application's functions which you want to profile and call them from a script. Structuring your application's internals as a library makes this easier.

### Visualizing .prof files with snakeviz

Once this completes, a profile with the name you specified will be saved to disk, and you can visualize it by typing:

```
snakeviz profile_name.prof
```

You can [download snakeviz from PyPI](https://pypi.org/project/snakeviz/). Its output is more limited than that of `samply`, but is more intuitive, and clearly shows the hierarchy of function calls and what dominates runtime.

!!! info
    While `samply` is quite efficient and should impose a relatively small penalty on your application's performance, cProfile is heavier and will slow down your application a good deal more, especially if it's CPU-intensive.

## Alternatives

In addition to these, you may consider using profilers such as [py-spy](https://pypi.org/project/py-spy) with visualizers like [speedscope](https://speedscope.app), which provide extremely detailed line-by-line profiling.

In conclusion: having profilers and samplers in your toolbox and using them during development allows you to quickly and easily determine where your program is spending time and diagnose performance issues.