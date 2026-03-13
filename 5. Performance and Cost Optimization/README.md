# Performance and Cost Optimization in Azure Cosmos DB

## Modules

1. **Understanding RU/s and Capacity Planning**  
   Learn how to plan for Request Units and choose the appropriate capacity for your application.  
   
2. **Query Optimization Strategies**  
   Explore techniques for optimizing your queries to improve performance and reduce cost.  
   
3. **Indexing Best Practices**  
   Understand how to create and manage indexes effectively to enhance query performance.  
   
4. **Partitioning Strategies**  
   Study how to partition your data for scalable performance and optimization.  
   
5. **Cost Optimization Techniques**  
   Discover methods to optimize your costs while using Azure Cosmos DB.  
   
6. **Quick Code Samples**  
   - Sample code demonstrating query optimization.  
   - Example of indexing rules for faster queries.  
   - Code snippets for partitioning demonstration.  

## Sample Outputs

### Query Performance Analysis Examples

1. **Sample output from explain() for Query 1:**  
   ```json
   {
     "queryMetrics": {
       "executionTime":"10ms",
       "retrievedDocumentCount": 5,
       "requestUnits": 2
     }
   }
   ```  

2. **Sample output from explain() for Query 2:**  
   ```json
   {
     "queryMetrics": {
       "executionTime":"20ms",
       "retrievedDocumentCount": 10,
       "requestUnits": 5
     }
   }
   ```  

3. **Sample output from explain() for Query 3:**  
   ```json
   {
     "queryMetrics": {
       "executionTime":"12ms",
       "retrievedDocumentCount": 2,
       "requestUnits": 3
     }
   }
   ```  
