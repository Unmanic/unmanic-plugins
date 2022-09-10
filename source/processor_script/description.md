
The script can be any command or script. If you choose to use a custom script, be sure to make the script executable before trying to use it.

Enable debug logging to see the output of your configured command or script in the Unmanic log file.

---

##### Links:

- [Support](https://unmanic.app/discord)
- [Issues/Feature Requests](https://github.com/Unmanic/plugin.processor_script/issues)
- [Pull Requests](https://github.com/Unmanic/plugin.processor_script/pulls)


---

##### Script Variables Template Substitutions:
The following template replacements are available to your command or args. 
If you write one of these variables in your args, it will be substituted with the specified data from the current task.

:::note
Variable substitutions are not applied to the script, only a script's args.
:::

:::tip
In some cases, you may need to place single quotes around these variables as it may contain characters that shell may otherwise attempt to parse.
:::

###### <span style="color:green">{library_id}</span>

Will be replaced with the ID of the library config that was used to process this file.

Eg.
```
    --library='{library_id}'
```

###### <span style="color:green">{file_out_path}</span>

Will be replaced with the path to the suggested output file in the Unmanic cache directory for this task.

:::note
If no file is output to this file after executing the script, the input file will be used again for the next plugins input file.
If your script needs to modify the file out path (eg, the script has modified the file to a new file extension.), 
then use the '{data_json_file}' variable described below.
:::

Eg.
```
    --output-cache-file='{file_out_path}'
```

###### <span style="color:green">{original_file_path}</span>

Will be replaced with the full path to the original source file in your library.

Eg.
```
    --original-source-file='{original_file_path}'
```

###### <span style="color:green">{original_file_size}</span>

Will be replaced with the size in bytes of the original source file in your library.

Eg.
```
    --original-source-size='{source_file_size}'
```

###### <span style="color:green">{source_file_path}</span>

Will be replaced with the full path to the current file to be processed by this task. 

If this plugin is being executed first on the library file, then this will be the same as the '{original_file_path}'.
If not, then this plugin will be taking as input a cached file that was the output from the previous plugins command.

Eg.
```
    --source-file='{source_file_path}'
```

###### <span style="color:green">{source_file_size}</span>

Will be replaced with the size in bytes of the current source file for this task.

Eg.
```
    --source-size='{source_file_size}'
```

###### <span style="color:green">{data_json_file}</span>

Will be replaced with the path to a data file. 
Your script can dump JSON data to this file and this plugin will use this data to update the following return parameters.

- exec_command
- file_in
- file_out
- repeat

Eg.
```
    --return-data-file='{data_json_file}'`
```

---

##### Examples:

###### <span style="color:magenta">Create a TAR archive from the task file</span>
**<span style="color:blue">Execution Type</span>**
> *Bash Script*

**<span style="color:blue">Script:</span>**
```bash
for arg in ${@}; do
    case ${arg} in
        --infile*)
            infile=$(echo ${arg} | awk -F'=' '{print $2}');
            ;;
        --outfile*)
            outfile=$(echo ${arg} | awk -F'=' '{print $2}');
            ;;
        --datafile*)
            datafile=$(echo ${arg} | awk -F'=' '{print $2}');
            ;;
        *) 
            ;;
    esac
done

tar_outfile=${outfile}.tar.gz

tar czf "${tar_outfile}" "${infile}"

cat << EOF > "${datafile}"
{
    "file_out": "${tar_outfile}"
}
EOF
```

**<span style="color:blue">Args:</span>**
```
--infile='{source_file_path}'
--outfile='{file_out_path}'
--datafile='{data_json_file}'
```
