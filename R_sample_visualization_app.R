#R_sample_visualization_app.R
#Jaehoon Ahn 

#New fix marked by #+++++
#Codes commented #!!!!! requires fixing/attention
#LG: Time-series
#BC: Bar-plot 

library(shiny)
library(readxl)
library(ggplot2) 
library(plotly)
library(shinythemes)
library(dplyr)
library(stringr)
library(reshape2)
library(scales)


#Update the helperFunctions.R to match the version you are workign on 
source("R_sample_visualization_app_helperfunctions.R")


############################################################
##################USER INTERFACE############################
############################################################


ui <- navbarPage( "Interactive DataViz",
  #Color theme 
  theme = shinytheme("spacelab"),

  #Home tab 
  tabPanel("Home", 
           mainPanel(
             code(h1("Interactive Data Visualization Tool")),
             h3("Use Shiny with Ease")
           )), 
  
  #Data input tab 
  tabPanel("Data",
           titlePanel("Upload Data"),
           sidebarLayout(
             sidebarPanel(
               #Input: ".xlsx" file 
               fileInput("file", "Choose Excel File",
                         multiple = FALSE,
                         accept = c(".xls", ".xlsx", ".xlsm")
                          ),
               tags$hr()
             ),
             mainPanel(
               verbatimTextOutput("dataset_list_str") 
             )
           )
  ),

  #Line Graph tab 
  tabPanel("Line Graph",
    titlePanel("Line Graph"),
    sidebarLayout(
      sidebarPanel(
        uiOutput("select_LG_dataset"),
        uiOutput("select_LG_variable"),
        uiOutput("select_LG_subVariable")
      ),
      mainPanel(
        uiOutput("LGgraphs")
      )
    )
  ),


  #Bar-plot graph tab 
  tabPanel("Bar Chart",
    titlePanel("Bar Chart"),
    sidebarLayout(
      sidebarPanel(
         uiOutput("select_BC_dataset"),
         uiOutput("select_BC_var"),
         uiOutput("yaxis_singleBC")  
      ),
      mainPanel(
        plotlyOutput("BCgraphs")
      )
    )
  ),
  
  #User documentation and help tab 
  tabPanel("Help"),
  
  #Suppresses all error messages 
  tags$style(type="text/css",
             ".shiny-output-error { visibility: hidden; }",
             ".shiny-output-error:before { visibility: hidden; }"
  )
)


############################################################
##################SERVER BACKEND############################
############################################################


server <- function(input, output){
  
  ##################
  #Reactive objects#
  ##################
  
  #Reactive object: Creates list of sheet dataframes from input Excel file
  #Reads in task 1 and task 2 data differently
  #Input: User-selected Excel file in SHINY app 
  #Output: Reactive dataset_list object 
  dataset_list <- reactive({
    inFile <- input$file
    
    if(is.null(inFile)){
      return("No file selected")
    }
    
    file.rename(inFile$datapath, paste(inFile$datapath, ".xlsx", sep=""))
    LGBC_list <- read_excel_allsheets(paste(inFile$datapath, ".xlsx", sep=""))
  })
  
   
  #Functions: Creates separate reative objects
  #!!!Is this the best way to set up multiple reactive objects? 
  LG_list <- reactive({dataset_list()$LG}) 
  LG_sheet <- reactive({LG_list()[[input$LG_dataset]]}) 

  selected_inputIndex <- reactive({
    seq(from = 1, to = length(LG_sheet()))[names(LG_sheet()) %in% input$LG_variable]
  })
  
  BC_list <- reactive({dataset_list()$BC})
  
  
  #############
  #Time-series#
  #############
  
  #Function: Lets user select time-series dataset (one excel time-series sheet)
  output$select_LG_dataset <- renderUI({
    selectInput("LG_dataset",
                label = "Select a line graph dataset:",
                choices = names(LG_list()),
                selected = (names(LG_list()))[1]
    )
  })
  
  
  #Function: Lets user select time-series variable 
  output$select_LG_variable <- renderUI({
    if (str_sub(input$LG_dataset, -1) == "m" | str_sub(input$LG_dataset, -1) == "M") {
      LG_var <- names(LG_sheet())
    } else {
      LG_var <- names(LG_sheet())[-1]
    }
    checkboxGroupInput("LG_variable", 
                       label = "Select a variable:", 
                       choices = LG_var
    )
  })
  
  
  #Function: Lets user select time-series sub-variable 
  output$select_LG_subVariable <- renderUI({
    
    #If time-series multi dataset:
    if (str_sub(input$LG_dataset, -1) == "m" | str_sub(input$LG_dataset, -1) == "M") {
      
      sidebarPanelList <- list()

      
      #If one or more variable is selected...
      if (length(selected_inputIndex()) >= 1) {
        # Updates the number of lines within a selected plot
        for(i in selected_inputIndex()){ #!!!Clean this up a little and figure out why it works 
          dataset = LG_sheet()
          variable = names(dataset)[i]
          subvariable_list = names(dataset[[variable]])
          
          var_inputItem <- checkboxGroupInput(inputId = paste0("LG_var_cat", i), 
                                              label = paste("Select categories for Variable", i), 
                                              choices = subvariable_list[-1]
                                              )
          sidebarPanelList <- list(sidebarPanelList, var_inputItem)
        }
        # Allows for sidebarPanel to be created in Shiny
        do.call(tagList, sidebarPanelList) 
      }
    }
  })
  
  
  ##########
  #Bar-plot#
  ##########
  
  #Function: Lets user select bar-plot dataset (one excel bar-plot sheet) 
  output$select_BC_dataset <- renderUI({
    selectInput("BC_dataset",
                label = "Select a bar chart dataset:",
                choices = names(dataset_list()$BC),
                selected = (names(dataset_list()$BC))[1]
    )
  })
  
  
  #Function: Lets user select bar-plot variable 
  output$select_BC_var <- renderUI({
    
    selectInput("BC_var", 
                label = "Select a variable:", 
                choices = (names(BC_list()[[input$BC_dataset]]))[c(-1)], 
                selected = (names(BC_list()[[input$BC_dataset]]))[2]
    )
  })
  
  
  #Function: Lets user control single bar-plot y-axis 
  output$yaxis_singleBC <- renderUI({
    dataset <- BC_list()[[input$BC_dataset]]
    var_data <- dataset[[input$BC_var]]
    # Find a range of y's that'll leave sufficient space above the tallest bar
    ylim <- 1.3*max(var_data)
    
    sliderInput(inputId = "yaxis_singleBC",
                label = "Y-Axis",
                min = 0,
                max = round(ylim * 1.2, digits = 0),
                value = ylim)
  })
  
  
  #######################
  #Graphing: Time-series#
  #######################
  
  #Main-panel time-series graph outputs 
  #+++++ output$graphs -> output$LGgraphs 
  output$LGgraphs <- renderUI({
    
    #multiple plot 
    if (str_sub(input$LG_dataset, -1) == "m" | str_sub(input$LG_dataset, -1) == "M") { 
      tabsetPanel(type = "tabs",
                  #+++++multi_plots -> multiPlots 
                  tabPanel("Graphic", uiOutput("multiPlots"))
      )
    
    #single plot   
    } else{ 
      tabsetPanel(type = "tabs",
                  tabPanel("Graphic", plotlyOutput(outputId = "single_LGplot", height = 800))
      )
    }
  })

  
  #Time-series single plot  
  #Transforms data into plotly long data format 
  LGdataset_long <- reactive({ dataMeltFun(input$LG_variable, LG_sheet()) }) 
  #Plugs long data into plotly graph 
  plotInput <-   reactive({LG_ggPlotly(LGdataset_long(), denseData = TRUE, title=input$LG_variable)})
  output$single_LGplot <- renderPlotly({print(plotInput())})
  
  
  #Time-series multiple plot  
  output$multiPlots <- renderUI({
    # Reactive function that aligns variable input and datasets
    updatePlots()
    # Updates datasets that appear in main panel 
    get_plot_output_list(selected_inputIndex()) 
  })
  
  
  #Makes plotly objects of all LG multi-plot user-selected variables 
  updatePlots <- reactive({
    
    for(i in selected_inputIndex()){
      multi_dataset = LG_sheet()
      variable = names(multi_dataset)[i]
      var_dataset = multi_dataset[[variable]]
      
      local({
        plotname <- paste0("Variable ", i)
        dataset_long <- 
          dataMeltFun(input[[paste0("LG_var_cat", i)]], var_dataset, multiplePlots=TRUE)
        
        
        output[[plotname]] <- renderPlotly({ 
          LG_ggPlotly(dataset_long, width = 600, height = 400, denseData = TRUE, title = plotname)
        })
      })
    }
  })

  
  #####################
  #Graphing: Bar-plots#
  #####################
  
  #Draws graph2 bar plots 
  output$BCgraphs <- renderPlotly({
    BC_ggplotly(dataset_list = dataset_list()$BC, data_input = input$BC_dataset, 
                    var_input = input$BC_var, yaxis_input = input$yaxis_singleBC)
  })
}  
 
#Run Shiny App
shinyApp(ui=ui, server)
 
