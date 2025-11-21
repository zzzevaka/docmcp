import React from 'react'
import * as AccordionPrimitive from '@radix-ui/react-accordion'
import { ChevronRight } from 'lucide-react'
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const treeVariants = cva(
    'group hover:before:opacity-100 before:absolute before:rounded-lg before:left-0 px-2 before:w-full before:opacity-0 before:bg-accent/70 before:h-[2rem] before:-z-10'
)

const selectedTreeVariants = cva('before:opacity-100 before:bg-accent/70 text-accent-foreground')

const dragOverVariants = cva('before:opacity-100 before:bg-primary/20 text-primary-foreground')

const TreeView = React.forwardRef((
    {
        data,
        initialSelectedItemId,
        onSelectChange,
        expandAll,
        defaultLeafIcon,
        defaultNodeIcon,
        className,
        onDocumentDrag,
        renderItem,
        ...props
    },
    ref
) => {
    const [selectedItemId, setSelectedItemId] = React.useState(initialSelectedItemId)

    const [draggedItem, setDraggedItem] = React.useState(null)

    const handleSelectChange = React.useCallback((item) => {
        setSelectedItemId(item?.id)
        if (onSelectChange) {
            onSelectChange(item)
        }
    }, [onSelectChange])

    const handleDragStart = React.useCallback((item) => {
        setDraggedItem(item)
    }, [])

    const handleDrop = React.useCallback((targetItem, dropZone = 'on') => {
        if (draggedItem && onDocumentDrag && draggedItem.id !== targetItem.id) {
            onDocumentDrag(draggedItem, targetItem, dropZone)
        }
        setDraggedItem(null)
    }, [draggedItem, onDocumentDrag])

    const expandedItemIds = React.useMemo(() => {
        if (!initialSelectedItemId) {
            return [];
        }

        const ids = []

        function walkTreeItems(
            items,
            targetId
        ) {
            if (Array.isArray(items)) {
                for (let i = 0; i < items.length; i++) {
                    ids.push(items[i].id)
                    if (walkTreeItems(items[i], targetId) && !expandAll) {
                        return true
                    }
                    if (!expandAll) ids.pop()
                }
            } else if (!expandAll && items.id === targetId) {
                return true
            } else if (items.children) {
                return walkTreeItems(items.children, targetId);
            }
        }

        walkTreeItems(data, initialSelectedItemId)
        return ids
    }, [data, expandAll, initialSelectedItemId])

    return (
        <div className={cn('overflow-hidden relative p-2', className)}>
            <TreeItem
                data={data}
                ref={ref}
                selectedItemId={selectedItemId}
                handleSelectChange={handleSelectChange}
                expandedItemIds={expandedItemIds}
                defaultLeafIcon={defaultLeafIcon}
                defaultNodeIcon={defaultNodeIcon}
                handleDragStart={handleDragStart}
                handleDrop={handleDrop}
                draggedItem={draggedItem}
                renderItem={renderItem}
                level={0}
                {...props} />
            <div
                className='w-full h-[48px]'
                onDrop={() => { handleDrop({id: '', name: 'parent_div'})}}>
            </div>
        </div>
    );
})
TreeView.displayName = 'TreeView'

const TreeItem = React.forwardRef((
    {
        className,
        data,
        selectedItemId,
        handleSelectChange,
        expandedItemIds,
        defaultNodeIcon,
        defaultLeafIcon,
        handleDragStart,
        handleDrop,
        draggedItem,
        renderItem,
        level,
        onSelectChange,
        expandAll,
        initialSelectedItemId,
        onDocumentDrag,
        ...props
    },
    ref
) => {
    if (!(Array.isArray(data))) {
        data = [data]
    }

    const [isDropZoneActive, setIsDropZoneActive] = React.useState(false)

    const handleTopDropZoneDragOver = (e) => {
        if (draggedItem && level === 0) {
            e.preventDefault()
            setIsDropZoneActive(true)
        }
    }

    const handleTopDropZoneDragLeave = () => {
        setIsDropZoneActive(false)
    }

    const handleTopDropZoneDrop = (e) => {
        e.preventDefault()
        setIsDropZoneActive(false)
        if (draggedItem && data.length > 0 && level === 0) {
            // Drop before the first element
            handleDrop?.(data[0], 'before')
        }
    }

    return (
        <div ref={ref} role="tree" className={className} {...props}>
            {/* Drop zone before first element (only on top level) */}
            {level === 0 && data.length > 0 && (
                <div
                    className={`h-8 -mb-8 relative ${isDropZoneActive ? 'bg-blue-50' : ''}`}
                    onDragOver={handleTopDropZoneDragOver}
                    onDragLeave={handleTopDropZoneDragLeave}
                    onDrop={handleTopDropZoneDrop}
                >
                    {isDropZoneActive && (
                        <div className="absolute top-0 left-0 right-0 h-1 bg-blue-500 rounded" />
                    )}
                </div>
            )}
            <ul>
                {data.map((item) => (
                    <li key={item.id}>
                        {item.children ? (
                            <TreeNode
                                item={item}
                                level={level ?? 0}
                                selectedItemId={selectedItemId}
                                expandedItemIds={expandedItemIds}
                                handleSelectChange={handleSelectChange}
                                defaultNodeIcon={defaultNodeIcon}
                                defaultLeafIcon={defaultLeafIcon}
                                handleDragStart={handleDragStart}
                                handleDrop={handleDrop}
                                draggedItem={draggedItem}
                                renderItem={renderItem} />
                        ) : (
                            <TreeLeaf
                                item={item}
                                level={level ?? 0}
                                selectedItemId={selectedItemId}
                                handleSelectChange={handleSelectChange}
                                defaultLeafIcon={defaultLeafIcon}
                                handleDragStart={handleDragStart}
                                handleDrop={handleDrop}
                                draggedItem={draggedItem}
                                renderItem={renderItem} />
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
})
TreeItem.displayName = 'TreeItem'

const TreeNode = ({
    item,
    handleSelectChange,
    expandedItemIds,
    selectedItemId,
    defaultNodeIcon,
    defaultLeafIcon,
    handleDragStart,
    handleDrop,
    draggedItem,
    renderItem,
    level = 0
}) => {
    const [value, setValue] = React.useState(expandedItemIds.includes(item.id) ? [item.id] : [])
    const [dropZone, setDropZone] = React.useState(null) // 'before', 'on', 'after'
    const elementRef = React.useRef(null)
    const hasChildren = !!item.children?.length
    const isSelected = selectedItemId === item.id
    const isOpen = value.includes(item.id)

    const onDragStart = (e) => {
        if (!item.draggable) {
            e.preventDefault()
            return
        }
        e.dataTransfer.setData('text/plain', item.id)
        handleDragStart?.(item)
    }

    const getDropZone = (e) => {
        if (!elementRef.current) return 'on'
        const rect = elementRef.current.getBoundingClientRect()
        const y = e.clientY - rect.top
        const height = rect.height

        // Divide element into 3 zones: top 33%, middle 34%, bottom 33%
        if (y < height * 0.33) return 'before'
        if (y > height * 0.67) return 'after'
        return 'on'
    }

    const onDragOver = (e) => {
        if (item.droppable !== false && draggedItem && draggedItem.id !== item.id) {
            e.preventDefault()
            const zone = getDropZone(e)
            setDropZone(zone)
        }
    }

    const onDragLeave = () => {
        setDropZone(null)
    }

    const onDrop = (e) => {
        e.preventDefault()
        const zone = dropZone
        setDropZone(null)
        handleDrop?.(item, zone)
    }

    return (
        <AccordionPrimitive.Root type="multiple" value={value} onValueChange={(s) => setValue(s)}>
            <AccordionPrimitive.Item value={item.id}>
                <div className="relative" ref={elementRef}>
                    {dropZone === 'before' && (
                        <div className="absolute top-0 left-0 right-0 h-1 bg-blue-500 z-10 rounded" />
                    )}
                    {dropZone === 'after' && (
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-500 z-10 rounded" />
                    )}
                    <AccordionTrigger
                        className={cn(
                            treeVariants(),
                            isSelected && selectedTreeVariants(),
                            dropZone === 'on' && dragOverVariants(),
                            item.className
                        )}
                        onClick={() => {
                            handleSelectChange(item)
                            item.onClick?.()
                        }}
                        draggable={!!item.draggable}
                        onDragStart={onDragStart}
                        onDragOver={onDragOver}
                        onDragLeave={onDragLeave}
                        onDrop={onDrop}>
                    {renderItem ? (
                        renderItem({
                            item,
                            level,
                            isLeaf: false,
                            isSelected,
                            isOpen,
                            hasChildren,
                        })
                    ) : (
                        <>
                            <TreeIcon
                                item={item}
                                isSelected={isSelected}
                                isOpen={isOpen}
                                default={defaultNodeIcon} />
                            <span className="text-sm truncate">{item.name}</span>
                            <TreeActions isSelected={isSelected}>
                                {item.actions}
                            </TreeActions>
                        </>
                    )}
                </AccordionTrigger>
                </div>
                <AccordionContent className="ml-4 pl-1 border-l">
                    <TreeItem
                        data={item.children ? item.children : item}
                        selectedItemId={selectedItemId}
                        handleSelectChange={handleSelectChange}
                        expandedItemIds={expandedItemIds}
                        defaultLeafIcon={defaultLeafIcon}
                        defaultNodeIcon={defaultNodeIcon}
                        handleDragStart={handleDragStart}
                        handleDrop={handleDrop}
                        draggedItem={draggedItem}
                        renderItem={renderItem}
                        level={level + 1} />
                </AccordionContent>
            </AccordionPrimitive.Item>
        </AccordionPrimitive.Root>
    );
}

const TreeLeaf = React.forwardRef((
    {
        className,
        item,
        level,
        selectedItemId,
        handleSelectChange,
        defaultLeafIcon,
        handleDragStart,
        handleDrop,
        draggedItem,
        renderItem,
        ...props
    },
    ref
) => {
    const [dropZone, setDropZone] = React.useState(null)
    const elementRef = React.useRef(null)
    const isSelected = selectedItemId === item.id

    const onDragStart = (e) => {
        if (!item.draggable || item.disabled) {
            e.preventDefault()
            return
        }
        e.dataTransfer.setData('text/plain', item.id)
        handleDragStart?.(item)
    }

    const getDropZone = (e) => {
        if (!elementRef.current) return 'on'
        const rect = elementRef.current.getBoundingClientRect()
        const y = e.clientY - rect.top
        const height = rect.height

        // Divide element into 3 zones: top 33%, middle 34%, bottom 33%
        if (y < height * 0.33) return 'before'
        if (y > height * 0.67) return 'after'
        return 'on'
    }

    const onDragOver = (e) => {
        if (item.droppable !== false && !item.disabled && draggedItem && draggedItem.id !== item.id) {
            e.preventDefault()
            const zone = getDropZone(e)
            setDropZone(zone)
        }
    }

    const onDragLeave = () => {
        setDropZone(null)
    }

    const onDrop = (e) => {
        if (item.disabled) return
        e.preventDefault()
        const zone = dropZone
        setDropZone(null)
        handleDrop?.(item, zone)
    }

    return (
        <div className="relative" ref={elementRef}>
            {dropZone === 'before' && (
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-blue-500 z-10" />
            )}
            {dropZone === 'after' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 z-10" />
            )}
            <div
                ref={ref}
                className={cn(
                    'ml-5 flex text-left items-center py-2 cursor-pointer before:right-1',
                    treeVariants(),
                    className,
                    isSelected && selectedTreeVariants(),
                    dropZone === 'on' && dragOverVariants(),
                    item.disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
                    item.className
                )}
                onClick={() => {
                    if (item.disabled) return
                    handleSelectChange(item)
                    item.onClick?.()
                }}
                draggable={!!item.draggable && !item.disabled}
                onDragStart={onDragStart}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                {...props}>
            {renderItem ? (
                <>
                    <div className="h-4 w-4 shrink-0 mr-1" />
                    {renderItem({
                        item,
                        level,
                        isLeaf: true,
                        isSelected,
                        hasChildren: false,
                    })}
                </>
            ) : (
                <>
                    <TreeIcon item={item} isSelected={isSelected} default={defaultLeafIcon} />
                    <span className="flex-grow text-sm truncate">{item.name}</span>
                    <TreeActions isSelected={isSelected && !item.disabled}>
                        {item.actions}
                    </TreeActions>
                </>
            )}
            </div>
        </div>
    );
})
TreeLeaf.displayName = 'TreeLeaf'

const AccordionTrigger = React.forwardRef(({ className, children, ...props }, ref) => (
    <AccordionPrimitive.Header>
        <AccordionPrimitive.Trigger
            ref={ref}
            className={cn(
                'flex flex-1 w-full items-center py-2 transition-all first:[&[data-state=open]>svg]:first-of-type:rotate-90',
                className
            )}
            {...props}>
            <ChevronRight
                className="h-4 w-4 shrink-0 transition-transform duration-200 text-accent-foreground/50 mr-1" />
            {children}
        </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
))
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName

const AccordionContent = React.forwardRef(({ className, children, ...props }, ref) => (
    <AccordionPrimitive.Content
        ref={ref}
        className={cn(
            'overflow-hidden text-sm transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down',
            className
        )}
        {...props}>
        <div className="pb-1 pt-0">{children}</div>
    </AccordionPrimitive.Content>
))
AccordionContent.displayName = AccordionPrimitive.Content.displayName

const TreeIcon = ({
    item,
    isOpen,
    isSelected,
    default: defaultIcon
}) => {
    let Icon = defaultIcon
    if (isSelected && item.selectedIcon) {
        Icon = item.selectedIcon
    } else if (isOpen && item.openIcon) {
        Icon = item.openIcon
    } else if (item.icon) {
        Icon = item.icon
    }
    return Icon ? (
        <Icon className="h-4 w-4 shrink-0 mr-2" />
    ) : (
        <></>
    );
}

const TreeActions = ({
    children,
    isSelected
}) => {
    return (
        <div className="absolute right-3 flex items-center gap-0.5">
            {children}
        </div>
    );
}

export { TreeView, AccordionTrigger, AccordionContent, TreeLeaf, TreeNode, TreeItem };
